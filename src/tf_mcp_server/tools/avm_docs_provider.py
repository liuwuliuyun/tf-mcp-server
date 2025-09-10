"""
AVM provider documentation tools for Azure Terraform MCP Server.
"""

import csv
import io
import json
import logging
import os
import requests
import shutil
import tarfile
import time
import uuid

from ..core.config import Config

logger = logging.getLogger(__name__)

class Constants:
    AVAILABLE_MODULES_URL = "https://raw.githubusercontent.com/Azure/Azure-Verified-Modules/main/docs/static/module-indexes/TerraformResourceModules.csv"
    LOCAL_DATA_BASE_PATH = "__avm_data_cache__"
    AVAILABLE_MODULE_FILE = "available_modules.csv"
    CACHE_EXPIRATION_SECONDS = 86400  # 24 hours
    
    # Module CSV columns
    MODULE_NAME_COLUMN = "ModuleName"
    DESCRIPTION_COLUMN = "Description"
    MODULE_STATUS_COLUMN = "ModuleStatus"
    MODULE_STATUS_PROPOSED = "Proposed"
    MODULE_REPO_URL_COLUMN = "RepoURL"

    # Module Field Names
    MODULE_NAME_FIELD = "name"
    MODULE_DESCRIPTION_FIELD = "description"
    MODULE_SOURCE_FIELD = "source"
    MODULE_REPO_URL_FIELD = "repo_url"
    MODULE_AVAILABLE_VERSION_FIELD = "versions"

    # Version Field Names
    VERSION_TAG_NAME_FIELD = "tag_name"
    VERSION_CREATED_AT_FIELD = "created_at"
    VERSION_TARBALL_URL_FIELD = "tarball_url"


class ExpectedException(Exception):
    pass

class UnexpectedException(Exception):
    pass

def raise_expected_exception(message: str):
    logger.error(message)
    raise ExpectedException(message)

def raise_unexpected_exception(message: str):
    logger.error(message)
    raise UnexpectedException(message)

class AzureVerifiedModuleDocumentationProvider:
    def __init__(self):
        os.makedirs(Constants.LOCAL_DATA_BASE_PATH, exist_ok=True)
        self._available_modules: dict[str, dict] = None
    
    @staticmethod
    def _get_header() -> dict[str, str]:
        result = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        config = Config.from_env()
        if config and config.server and config.server.github_token:
            logger.info("Using GitHub token for authenticated requests.")
            result["Authorization"] = f"Bearer {config.server.github_token}"
        else:
            logger.warning("GitHub token is not set. You may encounter rate limiting when accessing GitHub API.")
        
        return result

    
    @staticmethod
    def _source_from_repo_url(repo_url: str) -> str:
        # Split https://github.com/Azure/terraform-azurerm-avm-res-apimanagement-service to get: ['https://github.com', 'Azure', 'terraform-azurerm-avm-res-apimanagement-service']
        _, github_org, module_repo_name = repo_url.rsplit('/', 2)
        # Split module name terraform-azurerm-avm-res-apimanagement-service to get: ['terraform', 'azurerm', 'avm-res-apimanagement-service'] 
        _, module_org, module_name = module_repo_name.split('-', 2)
        # Return format: "Azure/avm-res-apimanagement-service/azurerm"
        return f"{github_org}/{module_name}/{module_org}"
    
    @staticmethod
    def _download_module_version(source_url: str, target_path: str) -> None:
        try:
            response = requests.get(source_url, stream=True, headers=AzureVerifiedModuleDocumentationProvider._get_header())
            response.raise_for_status()

            uuid_str = str(uuid.uuid4())
            download_path = os.path.join(target_path, f"{uuid_str}.tar.gz")
            extract_to = target_path
            os.makedirs(extract_to, exist_ok=True)
            
            with open(download_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        
            # Extract the downloaded file
            with tarfile.open(download_path, "r:gz") as tar:
                # On Windows, extracting archives may fail due to path length limitations. See the Troubleshooting of README.md for details.
                tar.extractall(path=extract_to)
            os.remove(download_path)
            
            # re-organize the directory structure
            if len(os.listdir(extract_to)) == 1:
                src = os.path.join(extract_to, os.listdir(extract_to)[0])
                if os.path.isdir(src):
                    for entry in os.listdir(src):
                        shutil.move(os.path.join(src, entry), extract_to)
                    shutil.rmtree(src)
        except Exception as e:
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            raise_unexpected_exception(f"Failed to download module version from {source_url}: {e}")
    
    def _retrieve_version_info(self, module_name: str):
        available_modules = self._module_collection()
        if module_name not in available_modules:
            raise_expected_exception(f"Module {module_name} not found in available modules.")

        versions = dict()
        response = requests.get('/'.join([available_modules[module_name][Constants.MODULE_REPO_URL_FIELD].replace("github.com", "api.github.com/repos"),'releases']), headers=AzureVerifiedModuleDocumentationProvider._get_header())
        response.raise_for_status()
        for version in response.json():
            tag_name = version[Constants.VERSION_TAG_NAME_FIELD].lstrip('v')
            versions[tag_name] = dict()
            versions[tag_name][Constants.VERSION_TAG_NAME_FIELD] = tag_name
            versions[tag_name][Constants.VERSION_CREATED_AT_FIELD] = version[Constants.VERSION_CREATED_AT_FIELD]
            versions[tag_name][Constants.VERSION_TARBALL_URL_FIELD] = version[Constants.VERSION_TARBALL_URL_FIELD]

        available_modules[module_name][Constants.MODULE_AVAILABLE_VERSION_FIELD] = versions

    def _retrieve_version_path(self, module_name: str, version: str) -> str:
        available_modules = self._module_collection()
        if module_name not in available_modules:
            raise_expected_exception(f"Module {module_name} not found in available modules.")
        
        if Constants.MODULE_AVAILABLE_VERSION_FIELD not in available_modules[module_name]:
            self._retrieve_version_info(module_name)

        if version not in available_modules[module_name][Constants.MODULE_AVAILABLE_VERSION_FIELD]:
            available_versions = self._module_version_list(module_name)
            raise_unexpected_exception(f"Version {version} not found for module {module_name}, available versions are: {', '.join(available_versions)}")

        path = os.path.join(Constants.LOCAL_DATA_BASE_PATH, module_name, version)
        if not os.path.exists(path):
            AzureVerifiedModuleDocumentationProvider._download_module_version(available_modules[module_name][Constants.MODULE_AVAILABLE_VERSION_FIELD][version][Constants.VERSION_TARBALL_URL_FIELD], path)
        
        return path
    
    def _module_version_list(self, module_name: str) -> list[str]:
        available_modules = self._module_collection()
        if module_name not in available_modules:
            raise_expected_exception(f"Module {module_name} not found in available modules.")
        
        if Constants.MODULE_AVAILABLE_VERSION_FIELD not in available_modules[module_name]:
            self._retrieve_version_info(module_name)
            
        available_versions = list(available_modules[module_name][Constants.MODULE_AVAILABLE_VERSION_FIELD].values())
        available_versions.sort(key=lambda x: x[Constants.VERSION_CREATED_AT_FIELD], reverse=True)
        return [item[Constants.VERSION_TAG_NAME_FIELD] for item in available_versions]
    
    def _module_collection(self) -> dict[str, dict]:        
        try:
            module_file_path = os.path.join(Constants.LOCAL_DATA_BASE_PATH, Constants.AVAILABLE_MODULE_FILE)
            if os.path.exists(module_file_path) and (time.time() - os.path.getmtime(module_file_path)) < Constants.CACHE_EXPIRATION_SECONDS:
                logger.info("Loading available modules from local cache...")
                if self._available_modules is not None:
                    return self._available_modules
                
                with open(module_file_path, 'r', encoding='utf-8') as f:
                    csv_content = f.read()
            else:
                logger.info("Fetching available modules from remote URL...")
                response = requests.get(Constants.AVAILABLE_MODULES_URL)
                response.raise_for_status()
                csv_content = response.text
                # Save the fresh content to the cache file
                with open(module_file_path, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
            
            dict_reader = csv.DictReader(io.StringIO(csv_content))
            available_modules = dict()
            for row in dict_reader:
                if row[Constants.MODULE_STATUS_COLUMN] == Constants.MODULE_STATUS_PROPOSED:
                    continue

                available_module = dict()
                available_module[Constants.MODULE_NAME_FIELD] = row[Constants.MODULE_NAME_COLUMN]
                available_module[Constants.MODULE_DESCRIPTION_FIELD] = row[Constants.DESCRIPTION_COLUMN]
                available_module[Constants.MODULE_REPO_URL_FIELD] = row[Constants.MODULE_REPO_URL_COLUMN]
                available_module[Constants.MODULE_SOURCE_FIELD] = AzureVerifiedModuleDocumentationProvider._source_from_repo_url(row[Constants.MODULE_REPO_URL_COLUMN])
                
                available_modules[row[Constants.MODULE_NAME_COLUMN]] = available_module

            self._available_modules = available_modules    
            return self._available_modules
        except Exception as e:
            raise_unexpected_exception(f"Error retrieving available modules: {e}")

    def available_modules(self) -> str:
        result = []
        for _, module in self._module_collection().items():
            result.append({
                "module_name": module[Constants.MODULE_NAME_FIELD],
                "description": module[Constants.MODULE_DESCRIPTION_FIELD],
                "source": module[Constants.MODULE_SOURCE_FIELD],
            })

        return json.dumps(result, indent=2)
    
    def latest_module_version(self, module_name: str) -> str:
        available_versions = self._module_version_list(module_name)
        if not available_versions:
            return f"No version found for module: {module_name}"

        return available_versions[0]
    
    def module_versions(self, module_name: str) -> str:
        versions = self._module_version_list(module_name)
        return json.dumps(versions, indent=2) if versions else f"No versions found for module: {module_name}"
    
    def module_variables(self, module_name: str, raw_version: str) -> str:
        version = raw_version.lstrip('v')
        base_path = self._retrieve_version_path(module_name, version)
        variable_files = [f for f in os.listdir(base_path) if f.endswith('.tf') and f.startswith('variable')]

        result = ""
        for variable_file in variable_files:
            with open(os.path.join(base_path, variable_file), 'r') as file:
                result += file.read() + "\n"
        
        return result

    def module_outputs(self, module_name: str, raw_version: str) -> str:
        version = raw_version.lstrip('v')
        base_path = self._retrieve_version_path(module_name, version)        
        output_files = [f for f in os.listdir(base_path) if f.endswith('.tf') and f.startswith('output')]

        result = ""
        for output_file in output_files:
            with open(os.path.join(base_path, output_file), 'r') as file:
                result += file.read() + "\n"
        
        return result


# Global instance
_avm_provider = None


def get_avm_documentation_provider() -> AzureVerifiedModuleDocumentationProvider:
    """Get the global AVM documentation provider instance."""
    global _avm_provider
    if _avm_provider is None:
        _avm_provider = AzureVerifiedModuleDocumentationProvider()
    return _avm_provider