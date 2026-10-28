// Curvas de aceleración estilo Windows para touchpad y ratón en KWin (Plasma 6.7).
//
// libinput admite un perfil de aceleración personalizado, pero KWin 6.7 solo
// ofrece «plano» y «adaptativo». Esta biblioteca se precarga en kwin_wayland
// (LD_PRELOAD) y, cada vez que KWin configura la velocidad o el perfil de un
// touchpad o ratón, aplica además el perfil personalizado. Sin archivo de
// configuración no hace nada; el ratón solo se toca si hay claves mouse_*.
//
// Curva: G(v) = gmin + (gmax - gmin) * (1 - exp(-v / tau)) píxeles por mm de
// dedo, con v la velocidad del dedo en mm/s. El adaptativo de libinput es casi
// constante (≈10,5 px/mm) entre 7 y 130 mm/s y luego multiplica hasta ≈55 px/mm;
// esta curva sube de forma continua. El control de velocidad de KDE escala la
// curva por 2^velocidad.
//
// Ratón: como Windows, trabaja en puntos del sensor y no en mm, así que el botón
// de DPI del ratón sigue cambiando la sensibilidad. M(v) = mgmin + (mgmax - mgmin)
// * (1 - exp(-v / mtau)) píxeles por punto, con v en puntos/ms. El adaptativo de
// libinput da 1 px/punto hasta 0,4 puntos/ms y 2 px/punto desde 1,3 puntos/ms
// (≈40 mm/s a 800 DPI): casi todo movimiento normal va a la ganancia máxima.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <libinput.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct curve {
	double gmin, gmax, tau;  // px/mm y mm/s
	double resolution;       // unidades del touchpad por mm (eje X)
	double scroll;           // px por mm al desplazar con dos dedos
	double mgmin, mgmax, mtau; // ratón: px/punto y puntos/ms (mgmin 0 = no tocar)
};

static int load_curve(struct curve *c)
{
	char path[4096];
	const char *xdg = getenv("XDG_CONFIG_HOME");
	const char *home = getenv("HOME");
	if (xdg && *xdg)
		snprintf(path, sizeof path, "%s/macos-setup/touchpad-curve.conf", xdg);
	else if (home)
		snprintf(path, sizeof path, "%s/.config/macos-setup/touchpad-curve.conf", home);
	else
		return 0;

	FILE *f = fopen(path, "r");
	if (!f)
		return 0;
	*c = (struct curve){ .gmin = 4, .gmax = 30, .tau = 180, .resolution = 0, .scroll = 10.5,
			     .mgmin = 0, .mgmax = 2, .mtau = 6 };
	char line[256];
	while (fgets(line, sizeof line, f)) {
		char key[64];
		double value;
		if (line[0] == '#' || sscanf(line, " %63[a-z_] = %lf", key, &value) != 2)
			continue;
		if (!strcmp(key, "gmin")) c->gmin = value;
		else if (!strcmp(key, "gmax")) c->gmax = value;
		else if (!strcmp(key, "tau")) c->tau = value;
		else if (!strcmp(key, "resolution")) c->resolution = value;
		else if (!strcmp(key, "scroll")) c->scroll = value;
		else if (!strcmp(key, "mouse_gmin")) c->mgmin = value;
		else if (!strcmp(key, "mouse_gmax")) c->mgmax = value;
		else if (!strcmp(key, "mouse_tau")) c->mtau = value;
	}
	fclose(f);
	// Valores absurdos dejarían el puntero inmóvil o disparado: mejor no aplicar nada.
	if (!(c->mgmin > 0 && c->mgmax >= c->mgmin && c->mtau > 0))
		c->mgmin = 0;
	if (!(c->resolution > 0 && c->gmin > 0 && c->gmax >= c->gmin && c->tau > 0 && c->scroll > 0))
		c->resolution = 0;
	return c->resolution > 0 || c->mgmin > 0;
}

static int is_touchpad(struct libinput_device *device)
{
	return libinput_device_config_tap_get_finger_count(device) > 0;
}

static int is_mouse(struct libinput_device *device)
{
	return !is_touchpad(device) && libinput_device_has_capability(device, LIBINPUT_DEVICE_CAP_POINTER) &&
	       libinput_device_config_accel_is_available(device);
}

// libinput_device_config_accel_apply llama por dentro a set_profile/set_speed:
// sin esta marca, interceptarlas de nuevo crearía una recursión infinita.
static __thread int applying;
// Cambiar de perfil devuelve la velocidad de libinput a 0: recordar la que pidió
// KDE para cada dispositivo.
static struct { struct libinput_device *device; double speed; } requested[16];

static void remember_speed(struct libinput_device *device, double speed)
{
	for (size_t i = 0; i < sizeof requested / sizeof *requested; i++)
		if (requested[i].device == device || !requested[i].device) {
			requested[i].device = device;
			requested[i].speed = speed;
			return;
		}
}

static double requested_speed(struct libinput_device *device)
{
	for (size_t i = 0; i < sizeof requested / sizeof *requested; i++)
		if (requested[i].device == device)
			return requested[i].speed;
	return libinput_device_config_accel_get_speed(device);
}

#define POINTS 51         // touchpad: de 0 a 500 mm/s; ratón: de 0 a 30 puntos/ms
#define STEP_MM_S 10.0
#define MOUSE_STEP 0.6

static void apply_curve(struct libinput_device *device, double speed)
{
	struct curve c;
	if (applying || !load_curve(&c))
		return;
	int touchpad = is_touchpad(device);
	if (touchpad ? c.resolution <= 0 : (!is_mouse(device) || c.mgmin <= 0))
		return;

	double scale = pow(2.0, speed);
	double step, motion[POINTS], constant[2];
	if (touchpad) {
		// Entrada: unidades del touchpad por ms; salida: píxeles por ms.
		step = STEP_MM_S * c.resolution / 1000.0;
		for (int i = 0; i < POINTS; i++) {
			double v = i * STEP_MM_S;
			double gain = scale * (c.gmin + (c.gmax - c.gmin) * (1.0 - exp(-v / c.tau)));
			motion[i] = gain * v / 1000.0;
		}
		// Desplazamiento y gestos: constante, igual que el filtro adaptativo actual.
		constant[0] = 0.0;
		constant[1] = c.scroll / c.resolution;
	} else {
		// Entrada: puntos del sensor por ms; salida: píxeles por ms.
		step = MOUSE_STEP;
		for (int i = 0; i < POINTS; i++) {
			double v = i * MOUSE_STEP;
			motion[i] = scale * (c.mgmin + (c.mgmax - c.mgmin) * (1.0 - exp(-v / c.mtau))) * v;
		}
		// Rueda y demás: sin aceleración (1 punto = 1 unidad), como el perfil plano.
		constant[0] = 0.0;
		constant[1] = 1.0;
	}

	struct libinput_config_accel *config =
		libinput_config_accel_create(LIBINPUT_CONFIG_ACCEL_PROFILE_CUSTOM);
	if (!config)
		return;
	applying = 1;
	if (libinput_config_accel_set_points(config, LIBINPUT_ACCEL_TYPE_MOTION, step, POINTS, motion) ==
		    LIBINPUT_CONFIG_STATUS_SUCCESS &&
	    libinput_config_accel_set_points(config, LIBINPUT_ACCEL_TYPE_SCROLL, 1.0, 2, constant) ==
		    LIBINPUT_CONFIG_STATUS_SUCCESS &&
	    libinput_config_accel_set_points(config, LIBINPUT_ACCEL_TYPE_FALLBACK, 1.0, 2, constant) ==
		    LIBINPUT_CONFIG_STATUS_SUCCESS)
	{
		enum libinput_config_status status = libinput_device_config_accel_apply(device, config);
		if (getenv("TOUCHPAD_CURVE_DEBUG"))
			fprintf(stderr, "touchpad-curve: %s velocidad=%.2f escala=%.2f -> %s (perfil %d)\n",
				libinput_device_get_name(device), speed, scale,
				status == LIBINPUT_CONFIG_STATUS_SUCCESS ? "aplicada" : "rechazada",
				libinput_device_config_accel_get_profile(device));
	}
	applying = 0;
	libinput_config_accel_destroy(config);
}

// Se precarga en el envoltorio de KWin para que sobreviva a sus reinicios, pero
// no debe heredarse en Xwayland ni en otros procesos que lance kwin_wayland.
__attribute__((constructor)) static void stop_inheritance(void)
{
	if (!strcmp(program_invocation_short_name, "kwin_wayland"))
		unsetenv("LD_PRELOAD");
}

enum libinput_config_status
libinput_device_config_accel_set_speed(struct libinput_device *device, double speed)
{
	static enum libinput_config_status (*real)(struct libinput_device *, double);
	if (!real)
		real = dlsym(RTLD_NEXT, "libinput_device_config_accel_set_speed");
	enum libinput_config_status status = real(device, speed);
	if (status == LIBINPUT_CONFIG_STATUS_SUCCESS) {
		if (!applying)
			remember_speed(device, speed);
		apply_curve(device, speed);
	}
	return status;
}

enum libinput_config_status
libinput_device_config_accel_set_profile(struct libinput_device *device,
					 enum libinput_config_accel_profile profile)
{
	static enum libinput_config_status (*real)(struct libinput_device *,
						   enum libinput_config_accel_profile);
	if (!real)
		real = dlsym(RTLD_NEXT, "libinput_device_config_accel_set_profile");
	enum libinput_config_status status = real(device, profile);
	if (status == LIBINPUT_CONFIG_STATUS_SUCCESS)
		apply_curve(device, requested_speed(device));
	return status;
}
