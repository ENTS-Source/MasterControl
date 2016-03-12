import logging
import os
import imp

def get_plugins(plugin_dir, module_name):
    plugins = []
    logger = logging.getLogger(__name__)

    module_name = "MCP_safe_module_name_" + module_name.replace('.', '_')

    plugin_files = []
    for plugin_file in os.listdir(plugin_dir):
        if (plugin_file.endswith('.py')):
            plugin_files.append(plugin_file)

    for plugin_file in plugin_files:
        plugin_path = os.path.join(plugin_dir, plugin_file)
        logger.info('Loading plugin: %s' % plugin_path)
        try:
            plugin = imp.load_source(module_name + plugin_file[:-3], plugin_path)
        except Exception as e:
            logger.error('Error loading plugin: %s' % plugin_path, exc_info=True)
        else:
            try:
                if hasattr(plugin, 'setup'):
                    plugin.setup()
                plugins.append(plugin)
            except Exception as e:
                logger.error('Error setting up plugin: %s' % plugin_path, exc_info=True)

    return plugins
