from pybuilder.core import use_plugin, init

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin("python.sphinx")

name = "statemanager"
default_task = ["analyze", "publish", "sphinx_generate_documentation"]


@init
def set_properties(project):
    project.depends_on_requirements("requirements.txt")
    project.set_property('distutils_classifiers', '5')
    project.set_property('coverage_threshold_warn', 80)
    project.set_property('overage_break_build', True)
    project.set_property('name', 'statemanager')
    project.set_property('version', '0.0.1')
    project.set_property('dir_dist', '$dir_target/dist/$name-$version')
    project.set_property('flake8_break_build', False)
    project.set_property('sphinx_output_dir', '$dir_target/reports/docs')
