# decorator from willie irc bot

def commands(*command_list):
	"""Decorator. Sets a command list for a callable.

    This decorator can be used to add multiple commands to one callable in a
    single line. The resulting match object will have the command as the first
    group, rest of the line, excluding leading whitespace, as the second group.
    Parameters 1 through 4, separated by whitespace, will be groups 3-6.

    Args:
        command: A string, which can be a regular expression.

    Returns:
        A function with a new command appended to the commands
        attribute. If there is no commands attribute, it is added.

    Example:
        @command("hello"):
            If the command prefix is "\.", this would trigger on lines starting
            with ".hello".

        @commands('j', 'join')
            If the command prefix is "\.", this would trigger on lines starting
            with either ".j" or ".join".

    """

	def add_attribute(function):
		if not hasattr(function, "commands"):
			function.commands = []
		function.commands.extend(command_list)

		return function
	return add_attribute
