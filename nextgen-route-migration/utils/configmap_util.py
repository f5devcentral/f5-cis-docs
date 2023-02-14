from copy import deepcopy
import pathlib
import yaml
from utils.constants import *


def generate_config_map_with_base_route_group(cis_config_params, namespace="kube-system", policy_cr="", output_path=""):
    script_dir = pathlib.Path(__file__).parent.resolve().parent
    template_path = str(script_dir) + BASE_ROUT_SPEC_TEMPLATE

    if output_path != "":
        output_dir = output_path
    else:
        output_dir = str(pathlib.Path(__file__).parent.resolve().parent) + "/" + DEFAULT_OUTPUT_DIR

    with open(template_path) as file:
        template_config = yaml.safe_load(file)
        global_template_config = deepcopy(template_config)

    global_template_config['metadata']['namespace'] = namespace
    global_template_config['metadata']['name'] = GLOBAL_ECM_NAME
    global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultRouteGroup']['vserverAddr'] = \
        cis_config_params[ROUTE_VS_ADDRESS]
    vs_name = DEFAULT_VS_NAME
    if ROUTE_HTTP_VS_NAME in cis_config_params:
        vs_name = cis_config_params[ROUTE_HTTP_VS_NAME]
    elif ROUTE_HTTPS_VS_NAME in cis_config_params:
        vs_name = cis_config_params[ROUTE_HTTPS_VS_NAME]
    global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultRouteGroup']['vserverName'] = vs_name

    # Default SSL
    default_ssl = False
    if DEFAULT_CLIENT_SSL in cis_config_params:
        global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultTLS']['clientSSL'] = \
            cis_config_params[DEFAULT_CLIENT_SSL]
        default_ssl = True
    else:
        del global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultTLS']['clientSSL']
    if DEFAULT_SERVER_SSL in cis_config_params:
        global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultTLS']['serverSSL'] = \
            cis_config_params[DEFAULT_SERVER_SSL]
        default_ssl = True
    else:
        del global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultTLS']['serverSSL']
    if default_ssl:
        global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultTLS']['reference'] = 'bigip'
    else:
        del global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultTLS']

    # TLS cipher
    tls_cipher = False
    if TLS_VERSION in cis_config_params:
        global_template_config['data']['extendedSpec']['baseRouteSpec']['tlsCipher']['tlsVersion'] = \
            cis_config_params[TLS_VERSION]
        tls_cipher = True
    else:
        del global_template_config['data']['extendedSpec']['baseRouteSpec']['tlsCipher']['tlsVersion']
    if CIPHER_GROUP in cis_config_params:
        global_template_config['data']['extendedSpec']['baseRouteSpec']['tlsCipher']['cipherGroup'] = \
            cis_config_params[CIPHER_GROUP]
        tls_cipher = True
    else:
        del global_template_config['data']['extendedSpec']['baseRouteSpec']['tlsCipher']['cipherGroup']
    if CIPHERS in cis_config_params:
        global_template_config['data']['extendedSpec']['baseRouteSpec']['tlsCipher']['ciphers'] = \
            cis_config_params[CIPHERS]
        tls_cipher = True
    else:
        del global_template_config['data']['extendedSpec']['baseRouteSpec']['tlsCipher']['ciphers']
    if not tls_cipher:
        del global_template_config['data']['extendedSpec']['baseRouteSpec']['tlsCipher']

    if policy_cr != "":
        global_template_config['data']['extendedSpec']['baseRouteSpec']['defaultRouteGroup']["policyCR"] = policy_cr

    # Update configmap data
    global_template_config['data'] = {
        k: yaml.safe_dump(v, indent=2, default_style=None, default_flow_style=False)
        for k, v in list(global_template_config['data'].items())
    }

    # Generate configmap
    with open(output_dir + GLOBAL_ECM_NAME + '.yaml', "w") as glb_file:
        glb_file.write(yaml.dump(global_template_config, default_flow_style=False))
