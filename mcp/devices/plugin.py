def command(command_arg):
	"""
		Decorator to set which command argument the plugin will be called for
    """

	def add_attribute(function):
		if not hasattr(function, "command"):
			function.command = command_arg
		return function
	return add_attribute
