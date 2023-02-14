import json
import logging
import subprocess
import yaml
import pathlib
from copy import deepcopy
from utils.constants import *


# Converts container args to a dict
def convert_container_args_to_dict(args: list) -> dict:
    if not args or len(args) == 0:
        return dict()
    key = None
    args_dict = dict()
    for kv in args:
        if key and ("--" not in kv):
            args_dict[key] = kv
            key = None
        elif "=" in kv:
            k_v = kv.split("=")
            args_dict[k_v[0].strip("--")] = k_v[1]
            key = None
        elif "--" in kv:
            key = kv.strip("--")
    return args_dict


# Read yaml file contents
def read_yaml(file_path: str) -> dict:
    if file_path == "":
        return dict()
    with open(file_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as ex:
            logging.error("Failed to load yaml")
            raise ex


# Read json file contents
def read_json(file_path: str) -> dict:
    if file_path == "":
        return dict()
    with open(file_path, "r") as stream:
        try:
            return json.load(stream)
        except Exception as ex:
            logging.error("Failed to load json file")
            raise ex


# Create yaml file
def create_yaml_file(data: dict, dest_path: str):
    with open(dest_path, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


# Get deployment resource using deployment name
def get_deploy_res_from_deploy(deploy_name: str) -> dict:
    try:
        ns_name = deploy_name.split("/")
        cis_deploy_ns = ns_name[0]
        cis_deploy_name = ""
        if len(ns_name) > 1:
            cis_deploy_ns = ns_name[0]
            cis_deploy_name = ns_name[1]
        cis_deploy_cmd_json = "kubectl -n {} get deploy/{} -o json".format(cis_deploy_ns, cis_deploy_name)
        cis_deploy_obj = json.loads(subprocess.check_output(cis_deploy_cmd_json, shell=True).decode())
        return cis_deploy_obj
    except Exception as ex:
        logging.error("Failed to fetch deployment")
        raise ex


# Prepare CIS config yaml for nextGen routes
def prepare_cis_config_for_nextgen_routes(config: dict, deploy_obj: dict) -> dict:
    if not deploy_obj or not config or len(config) == 0:
        return dict()
    try:
        # Remove legacy route specific parameters
        keys = ["manage-routes", "custom-client-ssl", "custom-server-ssl", "route-http-vserver", "route-https-vserver",
                "route-vserver-addr", "default-client-ssl", "default-server-ssl", "tls-version", "cipher-group", "ciphers"]
        for k in keys:
            if k in config:
                del config[k]
        # Add nextGenRoute specific parameters
        config["controller-mode"] = "openshift"
        config["route-spec-configmap"] = "kube-system/global-spec-config"
        # Update deployment obj with the new config parameters
        final_config_args = list()
        for k, v in config.items():
            final_config_args.append("--"+k+"="+v)
        deploy_obj["spec"]["template"]["spec"]["containers"][0]["args"] = final_config_args
    except Exception as ex:
        logging.error("Failed to prepare CIS deployment config for nextGen routes")
        raise ex


# Generate CIS deployment yaml
def generate_cis_deployment_yaml(data: dict, dest_path: str):
    try:
        with open(dest_path, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
    except Exception as ex:
        logging.error("Failed to create CIS deployment file")
        raise ex


# Generate  Policy CR yaml
def generate_policy_yaml(data: dict, dest_path: str):
    try:
        with open(dest_path, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
    except Exception as ex:
        logging.error("Failed to create policy CR yaml file")
        raise ex


# Fetch CIS config parameters from deployment object
def get_cis_args_from_deployment(cis_deploy_obj: dict) -> list:
    if not cis_deploy_obj:
        return list()
    if ("spec" not in cis_deploy_obj) or ("template" not in cis_deploy_obj["spec"]) or \
            ("spec" not in cis_deploy_obj["spec"]["template"]) or \
            ("containers" not in cis_deploy_obj["spec"]["template"]["spec"]):
        return list()
    containers = cis_deploy_obj["spec"]["template"]["spec"]["containers"]
    if len(containers) == 0 or "args" not in containers[0]:
        return list()
    return containers[0]["args"]


# Fetch policy features from as3 configmap object
def get_policy_from_cm_obj(cm_obj: dict) -> dict:
    if not cm_obj or "data" not in cm_obj or len(cm_obj["data"]) == 0:
        return dict()
    if "template" not in cm_obj["data"]:
        return dict()
    if "declaration" not in cm_obj["data"]["template"]:
        return dict()
    data = json.loads(cm_obj["data"]["template"])
    if not data or len(data) == 0:
        return dict()
    data = data["declaration"]
    for _, tenants in data.items():
        for _, shared in tenants.items():
            for vs_key, vs in shared.items():
                vs_name = vs_key
                data = vs
                break
            break
        break
    policy_cr = extract_policies(data, vs_name)
    if policy_cr:
        policy_cr['metadata']['namespace'] = cm_obj['metadata']['namespace']
    return policy_cr


# extract_policies reads the policy features from as3 object and return the policy CR dict
def extract_policies(vs_data: dict, vs_name: str) -> dict:
    script_dir = pathlib.Path(__file__).parent.resolve().parent
    template_path = str(script_dir) + POLICY_TEMPLATE
    with open(template_path) as file:
        template_config = yaml.safe_load(file)
        policy_template = deepcopy(template_config)
    policy_template["spec"] = dict()
    if "snat" in vs_data:
        policy_template["spec"]["snat"] = vs_data["snat"]

    if "policyWAF" in vs_data:
        policy_template["spec"]["l7Policies"] = dict()
        waf = get_policy_value(vs_data["policyWAF"])
        if waf != "":
            policy_template["spec"]["l7Policies"]["waf"] = waf

    if "profileBotDefense" in vs_data:
        policy_template["spec"]["l3Policies"] = dict()
        bot_defence = get_policy_value(vs_data["profileBotDefense"])
        if bot_defence != "":
            policy_template["spec"]["l3Policies"]["botDefense"] = bot_defence

    if "profileDOS" in vs_data:
        if "l3Policies" not in policy_template["spec"]:
            policy_template["spec"]["l3Policies"] = dict()
        profile_dos = get_policy_value(vs_data["profileDOS"])
        if profile_dos != "":
            policy_template["spec"]["l3Policies"]["dos"] = profile_dos

    if "policyFirewallEnforced" in vs_data:
        if "l3Policies" not in policy_template["spec"]:
            policy_template["spec"]["l3Policies"] = dict()
        firewall = get_policy_value(vs_data["policyFirewallEnforced"])
        if firewall != "":
            policy_template["spec"]["l3Policies"]["firewallPolicy"] = firewall

    if "iRules" in vs_data:
        irules = get_policy_value(vs_data["iRules"])
        if irules != "":
            policy_template["spec"]["iRules"] = dict()
            if "https" in vs_name.lower():
                policy_template["spec"]["iRules"]["secure"] = irules
            else:
                policy_template["spec"]["iRules"]["insecure"] = irules

    if "clientTLS" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        client_tls = get_policy_value(vs_data["clientTLS"])
        if client_tls != "":
            policy_template["spec"]["profiles"]["tcp"] = dict()
            policy_template["spec"]["profiles"]["tcp"]["client"] = client_tls

    if "serverTLS" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        server_tls = get_policy_value(vs_data["serverTLS"])
        if server_tls != "":
            if "tcp" not in policy_template["spec"]["profiles"]:
                policy_template["spec"]["profiles"]["tcp"] = dict()
            policy_template["spec"]["profiles"]["tcp"]["server"] = server_tls

    if "profileHTTP" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        http_profile = get_policy_value(vs_data["profileHTTP"])
        if http_profile != "":
            policy_template["spec"]["profiles"]["http"] = http_profile

    if "profileHTTP2" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        http2_profile = get_policy_value(vs_data["profileHTTP2"])
        if http2_profile != "":
            policy_template["spec"]["profiles"]["http2"] = http2_profile

    if "persistenceMethods" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        persistence_method = get_policy_value(vs_data["persistenceMethods"])
        if persistence_method != "":
            policy_template["spec"]["profiles"]["persistenceProfile"] = persistence_method

    if "securityLogProfiles" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        log_profiles = list()
        for lp in vs_data["securityLogProfiles"]:
            log_profiles.append(lp["bigip"])
        if log_profiles != "":
            policy_template["spec"]["profiles"]["logProfiles"] = log_profiles

    if "profileMultiplex" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        multiplex_profile = get_policy_value(vs_data["profileMultiplex"])
        if multiplex_profile != "":
            policy_template["spec"]["profiles"]["profileMultiplex"] = multiplex_profile

    if "profileL4" in vs_data:
        if "profiles" not in policy_template["spec"]:
            policy_template["spec"]["profiles"] = dict()
        profile_l4 = get_policy_value(vs_data["profileL4"])
        if profile_l4 != "":
            policy_template["spec"]["profiles"]["profileL4"] = profile_l4

    return policy_template


# returns the policy value by removing the bigip key from bigip path reference if specified
def get_policy_value(val) -> str:
    if not val:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, dict) and "bigip" in val:
        return val["bigip"]
    if isinstance(val, list) and len(val) != 0:
        return val[0]
    return ""