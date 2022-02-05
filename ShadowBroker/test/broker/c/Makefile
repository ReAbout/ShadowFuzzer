.PHONY: all test clean reallyclean

CFLAGS=-I../../../lib -I../../../src -Wall -Werror

PLUGIN_SRC = \
	auth_plugin.c \
	auth_plugin_pwd.c \
	auth_plugin_acl.c \
	auth_plugin_acl_sub_denied.c \
	auth_plugin_v2.c \
	auth_plugin_context_params.c \
	auth_plugin_msg_params.c \
	auth_plugin_extended_multiple.c \
	auth_plugin_extended_single.c \
	auth_plugin_extended_single2.c

PLUGINS = ${PLUGIN_SRC:.c=.so}

SRC = \
	08-tls-psk-pub.c \
	08-tls-psk-bridge.c

TESTS = ${SRC:.c=.test}


all : ${PLUGINS} ${TESTS}

${PLUGINS} : %.so: %.c
	$(CC) ${CFLAGS} -fPIC -shared $< -o $@


${TESTS} : %.test: %.c
	$(CC) ${CFLAGS} $< -o $@ ../../../lib/libmosquitto.so.1


reallyclean : clean
	-rm -f *.orig

clean :
	rm -f *.so *.test
