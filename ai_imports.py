import importlib
import os
import sys
import warnings
from types import SimpleNamespace
from typing import Optional
from jina.constants import __resources_path__

IMPORTED = SimpleNamespace()
IMPORTED.executors = False
IMPORTED.schema_executors = {}

# AI-Driven Package Recommendation
def recommend_package(missing_module):
    # Here, integrate a pre-trained model or an AI service that suggests alternative packages
    # For demonstration, we're using a mock recommendation
    recommendations = {
        "numpy": ["scipy", "pandas"],
        "tensorflow": ["torch", "keras"]
    }
    return recommendations.get(missing_module, [])

class ImportExtensions:
    """
    A context manager for wrapping extension import and fallback. 
    It guides the user to pip install the correct package by looking up extra-requirements.txt.
    """

    def __init__(
        self,
        required: bool,
        logger=None,
        help_text: Optional[str] = None,
        pkg_name: Optional[str] = None,
        verbose: bool = True,
    ):
        self._required = required
        self._tags = []
        self._help_text = help_text
        self._logger = logger
        self._pkg_name = pkg_name
        self._verbose = verbose

    def __enter__(self):
        return self

    def _check_v(self, v, missing_module):
        if (
            v.strip()
            and not v.startswith('#')
            and v.startswith(missing_module)
            and ':' in v
        ):
            return True

    def _find_missing_module_in_extra_req(self, missing_module):
        with open(
            os.path.join(__resources_path__, 'extra-requirements.txt'), encoding='utf-8'
        ) as fp:
            for v in fp:
                if self._check_v(v, missing_module):
                    missing_module, install_tags = v.split(':')
                    self._tags.append(missing_module)
                    self._tags.extend(vv.strip() for vv in install_tags.split(','))
                    break

    def _find_missing_module(self, exc_val):
        missing_module = self._pkg_name or exc_val.name
        missing_module = self._find_missing_module_in_extra_req(missing_module)
        return missing_module

    def _err_msg(self, exc_val, missing_module):
        if self._tags:
            from jina.helper import colored

            req_msg = colored('fallback to default behavior', color='yellow')
            if self._required:
                req_msg = colored('and it is required', color='red')
            err_msg = f'''Python package "{colored(missing_module, attrs='bold')}" is not installed, {req_msg}.
            You are trying to use a feature not enabled by your current Jina installation.'''

            avail_tags = ' '.join(
                colored(f'[{tag}]', attrs='bold') for tag in self._tags
            )
            err_msg += (
                f'\n\nTo enable this feature, use {colored("pip install jina[TAG]", attrs="bold")}, '
                f'where {colored("[TAG]", attrs="bold")} is one of {avail_tags}.\n'
            )

            # AI-Driven Package Recommendations
            alternative_packages = recommend_package(missing_module)
            if alternative_packages:
                alt_pkg_msg = "AI Suggests these alternatives: " + ", ".join(alternative_packages)
                err_msg += f"\n{colored(alt_pkg_msg, attrs='italic')}"

        else:
            err_msg = f'{exc_val.msg}'
        return err_msg

    def _log_critical(self, err_msg):
        if self._verbose and self._logger:
            self._logger.critical(err_msg)
            if self._help_text:
                self._logger.error(self._help_text)

    def _log_warning(self, err_msg):
        if self._verbose and self._logger:
            self._logger.warning(err_msg)
            if self._help_text:
                self._logger.info(self._help_text)

    def _raise_or_suppress(self, err_msg, exc_val):
        if self._verbose and not self._logger:
            warnings.warn(err_msg, RuntimeWarning, stacklevel=2)
        if self._required:
            self._log_critical(err_msg)
            raise exc_val
        else:
            self._log_warning(err_msg)
            return True  # suppress the error

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type != ModuleNotFoundError:
            return
        missing_module = self._find_missing_module(exc_val)
        err_msg = self._err_msg(exc_val, missing_module)
        return self._raise_or_suppress(err_msg, exc_val)


def _path_import(absolute_path: str):
    import importlib.util

    try:
        # I don't want to trust user path based on directory structure, "user_module", period
        default_spec_name = 'user_module'
        user_module_name = os.path.splitext(os.path.basename(absolute_path))[0]
        if user_module_name == '__init__':
            # __init__ cannot be used as a module name
            spec_name = default_spec_name
        elif user_module_name not in sys.modules:
            spec_name = user_module_name
        else:
            warnings.warn(
                f'''
            {user_module_name} shadows one of the built-in Python module names.
            It is imported as `{default_spec_name}.{user_module_name}`

            Affects:
            - Either, change your code from using `from {user_module_name} import ...`
              to `from {default_spec_name}.{user_module_name} import ...`
            - Or, rename {user_module_name} to another name
            '''
            )
            spec_name = f'{default_spec_name}.{user_module_name}'

        spec = importlib.util.spec_from_file_location(spec_name, absolute_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec_name] = module
        spec.loader.exec_module(module)
    except Exception as ex:
        # AI-driven error handling
        alternative_action = "Check if the file path is correct or if the module contains any syntax errors."
        raise ImportError(f'Cannot import module from {absolute_path}. {alternative_action}') from ex


class PathImporter:
    """The class to import modules from paths."""

    @staticmethod
    def add_modules(*paths):
        """
        Import modules from paths.

        :param paths: Paths of the modules.
        """

        # assume paths are Python module names
        not_python_module_paths = []
        for path in paths:
            if not os.path.isfile(path):
                try:
                    importlib.import_module(path)
                except ModuleNotFoundError:
                    not_python_module_paths.append(path)
                except:
                    raise
            else:
                not_python_module_paths.append(path)

        # try again, but assume they are file paths instead of module names
        from jina.jaml.helper import complete_path

        for m in not_python_module_paths:
            _path_import(complete_path(m))
