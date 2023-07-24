"""Main module.

First, change the X in name of the "groupX" folder to your group number.

To run this script in PyCharm:
 1. Right-click on this file in the file view.
 2. Select "More Run/Debug" > "Modify Run Configuration..."
 3. Change "Script path" to "Module name", and enter: "groupX" (with your number)
 4. Change the working directory to the base directory of your repository.
 5. Now you can always run this script by clicking the green play button in the IDE
    (without repeating the previous steps).

To run this script in a terminal:
 1. Change your working directory to the base directory of your repository.
 2. Execute:
    $ python -m groupX
"""

import logging

from networkx import petersen_graph

from group3 import engine, bot_easy

# Configure the logger:
logging.basicConfig(
    # Only warnings will be logged by default. Change the following line to
    # modify the log level if you want to generate more verbose output.
    # Useful values are 'INFO', 'WARNING' or 'ERROR'.
    level=logging.INFO,

    # Output will be printed to the terminal by default.
    # The following lines make it write to a file instead:
    filename='./game.log',
    filemode='w',
)

# Set up the game:
game = engine.Game(
    # The graph you'll play on. Take a look at
    # https://networkx.org/documentation/stable/reference/generators.html
    # for more, or write your own.
    graph=petersen_graph(),

    # The engines for each player. Replace one 'engine' with 'bot_easy' to play against the bot.
    robber_engine=engine,
    cops_engine=bot_easy,

    cops_count=3,
    max_rounds=100,
    timeout_init=None,
    timeout_step=None,
)

# Run the entire game:
game.run()
