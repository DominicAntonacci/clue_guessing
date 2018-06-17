# Clue Guessing
The code here is used to find the optimal guessing strategy for the
board game Clue. It implements a few common human strategies along
with a maximum likelihood estimator for the cards sitting in the
envelope.

# Clue Overview
Clue is a deduction based board game where players take turns guessing
the person, weapon and room that a murder took place in. The official
rules are available
[here](https://www.hasbro.com/common/instruct/Clue_(2002).pdf). In
this, "guesses" are equivalent to the official rule's "Suggestions".

The game revolves around a deck of 21 cards, consisting of six people,
six weapons, and nine rooms. At the beginning of the game, one random
person, weapon and room cards are placed in an envelope. This person,
weapon and room are the solution to the murder mystery. The remaining
18 cards are distributed evenly among the players.

Players take turns moving around the board and making guesses about
which cards are in the envelope. When a player is in a room, they can
make a guess about the person, weapon and room in the envelope. The
other players are asked consecutively if they can disprove the
person's guess. If so, they will reveal one card to the guesser that
disproves the guess. When making a guess, the player must use the room
they are currently in.

Once a player is confident they know which cards are in the envelope,
they are allowed to make an accusation on their turn guessing any
person, weapon and room. They immediately consult the envelope and
determine if their accusation was correct. If it is, they win the
game. If it is incorrect, they are eliminated.

# Information Gathering
Clue is primarily a game about gathering information to make a guess
about which cards are in the envelope. A player can get lucky and win
on their first guess (a 0.3% chance), but in general, the player that
gathers and applies the most information is going to win.

## Known Card Constraints
A known card constraint is when it is known a player has some
particular card. These occur when you make a guess and another player
reveals a card in their hand to disprove your guess. These also occur
at the beginning of the game when you get your hand. Any cards in your
hand cannot be in anyone else's hand nor the envelope.

Known card constraints directly reveal information about which cards
are in the envelope. If player 1 has the Wrench, then the Wrench
cannot be in the envelope. Many players already track this information
using the game-supplied notepads.

Of all the factual information, known cards provide the most
information about the game state. The primary downside is the rarity
of this information. Only one known card constraint comes up with each
of your guesses.

## Missing Card Constraints
A missing card constraint is when it is known a player does not have a
particular card. These occur when a player makes a guess and another
player indicates that they cannot disprove the guess. For example, if
player 1 guesses "Mr. Green with the Revolver in the Study", and
player 2 cannot disprove this guess, it is then known that player 2
does not have Mr. Green or the Revolver or the Study cards.

Missing card constraints are harder to incorporate into a guessing
system; they do not directly provide information about the cards in
the envelope. However, if it is known that many players do not have a
particular card, then the probability that the card is in the envelope
goes up.

Missing card constraints contain the least information, but are the
most numerous of all the factual information revealed. Every guess is
likely to generate a handful of these, regardless of the player making
the guess.

## Set Constraints
A set constraint is when it is known that a player has at least one of
a set of cards. These occur when other players make a guess and
someone else disproves it. For example, if Player 1 guesses
"Mrs. White with the Candlestick in the Kitchen", and Player 2
disproves it, Player 3 knows that Player 2 has "Mrs. White" or
"Candlestick" or "Kitchen" card. This constraint does not discount the
possibility that Player 2 may have any combination of those three
cards, only that it has at least one of them.

Set constraints are the hardest to incorporate into a guessing
system. It isn't immediately clear how a set constraint influences the
probability of a particular card being in the envelope. When combined
with missing card constraints, the benefit of set constraints is
clear. Using the previous example where Player 2 must have
"Mrs. White" or the "Candlestick" or the "Kitchen" card. If later in
the game Player 2 is known to not have "Mrs. White" and not have the
"Kitchen", then clearly Player 2 must have the "Candlestick".

Multiple set constraints can also suggest which cards may be in a
player's hand. If a player is known to have "Mrs. White" or the
Candlestick" or the "Kitchen" card, and is later known to have
"Mr. Green" or the "Revolver" or the "Kitchen" card, it is mostly
likely that the player has the "Kitchen" card because it occurs in
both set constraints. This is a much harder idea to apply for a human
player.

Optimal use of set constraints is likely outside the abilities of a
human player. The complexity of tracking how a given set constraint
influences the current player and other players is better left to a
computer.

### What If No-One Disproves a Guess
If a player makes a guess that no-one disproves, there are two
possible reasons. First, they may have guessed the cards in the
envelope. Second, they may have guessed cards in their hand (see
[Deceptive Guessing](#Deceptive Guessing) for reasons why this may
happen). Assuming the player wants to win, in the first case, they
will make an accusation and the game will end. If they don't make an
accusation, then they know that their guess is invalid, and thus they
can disprove their own guess.

Another way to think about is the player made a guess but not an
accusation, the guessed cards cannot be in the envelope. But, because
no-one disproved the guess, no-one else has the guessed
cards. Therefore, at least one of the guessed cards must be in the
original player's hand.

Under the assumption that all players want to win, if no-one disproves
a guess, it is known that the original guesser must have one of those
cards, creating a set constraint for the original player.

# Deceptive Guessing
Deceptive guessing is defined as intentionally guessing cards in your
own hand. This may be done to confuse other players, hide that you
know information, or extract specific information from a guess.

These tactics make it impossible in general to gather information
about a player based on their guess. With no knowledge about their
guessing system, no meaningful conclusions can be drawn about a
player's guess.

## Confusing Other Players
Some players may intentionally guess cards in their hand to try to
confuse the other people. For example, suppose a player only guessed
cards in their hand. No-one would disprove the guess and it would seem
like those cards are likely to be in the envelope. Other players may
now guess those cards again, thinking some of them must be correct.

While players may try this tactic, it will fail miserably against a
good information gathering system. When making this kind of guess, the
guesser will get no new information about the game state (they already
knew who had the guessed cards), but everyone else will learn that
no-one else has those cards.

## Hiding Known Information
Once a player knows one of the cards in the envelope, they may choose
to intentionally guess a card in the same category from their
hand. This way, other players may not pick up on which card is in the
envelope.

For example, if a player knows the "Knife" is in the envelope, but has
the "Rope" in their hand, they may choose to guess the "Rope" as the
weapon. The end result is the same: no other player can disprove the
guessed weapon,and then other players don't keep hearing the "Knife"
get guessed and may forget about it. Then, the player can use the
correct weapon when making an accusation.

This tactic is encouraged to be used. It doesn't impact the
information gleaned by the guesser and is effective at misleading
weaker players. It doesn't provide much benefit against a good
information gathering system as the information has likely already
been revealed, but it doesn't hurt to do.

## Extracting Specific Information
Players may intentionally guess cards from their hand in order to gain
more information about other cards.

One bad, but common, tactic is to go to a room that you have the card
for. Then, no-one can disprove the room and you are free to guess
every turn until you've figured out the person and weapon. Then, you
can try to find the correct room. This strategy is bad because the
room is the most difficult piece of information to obtain. There are
nine rooms as opposed to six weapons and people, and one must travel
to each room to guess it. This tactic will clue everyone else into the
correct person and weapon and lead to a rush to find the correct room.

### The Good Way
A much better tactic is the reverse of this: intentionally guess a
person and weapon from your hand. This will force the room to be
revealed to you. Then, you can quickly move to a new room and try
again until the correct room is found. Then you can hone in on the
person and weapon. If you don't have both a person and weapon, guess
what you can from your hand. The approach will work, but is slower.

This approach prioritizes information about rooms above all else
because it is the most difficult to obtain. As the game progresses
information will leak about the person and weapon from other people's
guesses. Once the correct room is found, there may only be a few
reasonable candidates to guess for the person and weapon.

This strategy hasn't been play-tested. It is likely to work well in 6
player games, where not all players can use this approach (only up to
five players can have both a person and a weapon). If everyone is
practicing the strategy, it may be sub-optimal.

# Simplifying Assumptions
The Clue simulator here works on some simplifying assumptions. The
board is entirely abstracted away. Instead, players take turns making
guesses and having those guesses disproved. After they make a guess,
they are given the chance to make an accusation. Players may guess any
room at any time (instead of having to guess the room they are
currently in).

For guessing systems, this simplified game is sufficient to determine
the relative performance of systems. A few modifications are needed to
be used in an actual game.

1. When making a guess, the room must be the room the player is
   in. This can be done by ignoring the recommended room from the
   guessing system, or by forcing the guessing system to choose a
   guess that includes that room.
1. Because a player has to move around to guess various rooms, a
   player may choose to make an accusation early before they are
   certain of the results. This will be discussed in more detail
   later. This gets into game theory and is outside the scope of this
   project.
