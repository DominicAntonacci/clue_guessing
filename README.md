# clue_guessing
The code here is used to find the optimal guessing strategy for the board game Clue. It implements a few common human strategies along with a maximum likelihood estimator for the cards sitting in the envelope.

# Clue Overview
Clue is a deduction based board game where players take turns guessing the person, weapon and room that a murder took place in. The official rules are available [here](https://www.hasbro.com/common/instruct/Clue_(2002).pdf).

The game revolves around a deck of 21 cards, consisting of six people, six weapons, and nine rooms. At the beginning of the game, one random person, weapon and room cards are placed in an envelope. This person, weapon and room are the solution to the murder mystery. The remaining 18 cards are distributed evenly among the players.

Players take turns moving around the board and making guesses about which cards are in the envelope. When a player is in a room, they can make a guess about the person, weapon and room in the envelope. The other players are asked consecutively if they can disprove the person's guess. If so, they will reveal one card to the guesser that disproves the guess. When making a guess, the player must use the room they are currently in.

Once a player is confident they know which cards are in the envelope, they are allowed to make an accusation on their turn guessing any person, weapon and room. They immediately consult the envelope and determine if their accusation was correct. If it is, they win the game. If it is incorrect, they are eliminated.

# Simplifying Assumptions
The Clue simulator here works on some simplifying assumptions. The board is entirely abstracted away. Instead, players take turns making guesses and having those guesses disproved. After they make a guess, they are given the chance to make an accusation. Players may guess any room at any time (instead of having to guess the room they are currently in).

For guessing systems, this simplified game is sufficient to determine the relative performance of systems. A few modifications are needed to be used in an actual game.

1. When making a guess, the room must be the room the player is in. This can be done by ignoring the recommended room from the guessing system, or by forcing the guessing system to choose a guess that includes that room.
1. Because a player has to move around to guess various rooms, a player may choose to make an accusation early before they are certain of the results. This will be discussed in more detail later. This gets into game theory and is outside the scope of this project.

# Information From Guesses
As guesses are made, information about each player's hands are revealed. An optimal guessing system will make maximal use of all the information revealed. For human players, collecting the information is straightfoward, but making use of it is more challenging. There are three kinds of information revealed: that a player has a particular card, that a player does not have a card, and that a player has at least one card from a guess.
