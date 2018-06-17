#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Framework to try different Clue guessing stragegies.

This framework does not support movement/requiring a player to guess in the
room it is in. Any player may guess anything.

Copyright (C) 2018 Dominic Antonacci

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

#%%
import random

import numpy as np

# All the cards defined here so everyone can use them.
PEOPLE = ('Colonel Mustard', 'Miss Scarlet', 'Professor Plum',
          'Mr. Green', 'Mrs. White', 'Mrs. Peacock')

WEAPONS = ('Rope', 'Lead Pipe', 'Knife', 'Wrench', 'Candlestick', 'Revolver')

ROOMS = ('Kitchen', 'Study', 'Conservatory', 'Hall', 'Dining Room',
         'Billiard Room', 'Lounge', 'Library', 'Ballroom')


class ClueController():
    """
    A class that handles dealing out all the cards and running players.
    """

    def __init__(self, players):
        """
        Creates a new object.

        :param players: A list of player objects.
        """

        self.players = players

        # Create the solution
        self.solution = [random.choice(PEOPLE),
                         random.choice(WEAPONS),
                         random.choice(ROOMS)]

        self.guess_list = []
        self.proof_list = []

        # Construct the remainder of the deck.
        deck = []
        deck.extend(PEOPLE)
        deck.extend(WEAPONS)
        deck.extend(ROOMS)
        deck.remove(self.solution[0])
        deck.remove(self.solution[1])
        deck.remove(self.solution[2])
        random.shuffle(deck)

        # Deal out the cards to each player.
        for (ix, card) in enumerate(deck):
            self.players[ix % self.num_players].getCard(card)

        # Indicate all the cards have been dealt
        for p in self.players:
            p.doneSetup()

    @property
    def num_players(self):
        """
        Returns the number of players in the game.
        """
        return len(self.players)

    def runPlayer(self, player_idx):
        """
        Allows one player to make a guess and accusation and passes data to
        all other players.

        :param player_idx: The index of the player to run.

        :returns: True if the player won the game.
        """

        guess = self.players[player_idx].makeGuess()

        if not self.validateGuess(guess):
            print('Player {} made an invalid guess {}. '
                  'Skipping their turn.'.format(player_idx, guess))
            return False
        self.guess_list.append(guess)

        # Disprove the accusation by going around to each player, stopping if
        # a player can disprove it.
        proof_list = self.disproveGuess(player_idx, guess)
        self.proof_list.append(proof_list)

        self.distributeInformation(player_idx, guess, proof_list)
        # Give eacy player the information from the round, only informing other
        # players that a card was shown.

        # Allow the player to make an accusation
        acc = self.players[player_idx].makeAccusation()

        if acc is not None:
            if not self.validateGuess(acc):
                print('Player {} made an invalid accusation {}. '
                      'Ignoring accusation'.format(player_idx, acc))
                return False
            if self.checkAccusation(acc):
                return True

        return False

    def disproveGuess(self, player_idx, guess):
        """
        Attempts to disprove the player's guess.

        :param player_idx: The index of the player.
        :param guess: The player's guess.

        :returns: A list of the resuls from each player. Each element will be
            a tuple of (guessing_player_idx, proof). If the player can not
            disprove the guess, proof will be None.
        """
        proof_list = []
        guessing_order = [(ix + player_idx) % self.num_players
                          for ix in range(1, self.num_players)]
        for ix in guessing_order:
            p = self.players[ix]
            proof = p.disproveGuess(guess)
            proof_list.append((ix, proof))
            if proof is not None:
                break

        return proof_list

    def distributeInformation(self, player_idx, guess, proof_list):
        """
        Distributes information from the guess and subsequent disproving.

        Only the guessing player gets the actual card that disproved their
        guess. All other players only know which player disproved the
        assumption.

        :param player_idx: The index of the player who guessed.
        :param guess: The guess that player made.
        :param proof_list: The proof generated by disproveGuess.
        """
        other_players_proof = proof_list.copy()
        if other_players_proof[-1][1] is not None:
            other_players_proof[-1] = (other_players_proof[-1][0], True)
        for (ix, p) in enumerate(self.players):
            if ix == player_idx:
                p.getGuessInformation(player_idx, guess, proof_list)
            else:
                p.getGuessInformation(player_idx, guess, other_players_proof)

    def checkAccusation(self, acc):
        """
        Checks if an accusation is correct.
        """

        return all(card in self.solution for card in acc)

    def validateGuess(self, guess):
        """
        Validates that a given guess contains a person in the first position,
        weapon in the second, and room in the third.

        This is also valid for accusations.

        :returns: True if the given guess is valid.
        """
        is_valid = (guess[0] in PEOPLE
                    and guess[1] in WEAPONS
                    and guess[2] in ROOMS)
        if not is_valid:
            import pdb
            pdb.set_trace()
            print('Invalid guess {}!'.format(guess))

        return is_valid

    def runRound(self):
        """
        Allows each player to make a guess and receive data about the guess.
        """

        for ix in range(self.num_players):
            # If the basic player is added, it won't try to guess anything.
            res = self.runPlayer(ix)
            if res:
                return ix

        return None

    def runGame(self):
        """
        Runs an entire game and prints out the winner.
        """

        res = None
        num_rounds = 0
        while res is None:
            res = self.runRound()
            num_rounds += 1

        print('Player {} won after {} rounds!'.format(res, num_rounds))
        return (res, num_rounds)

#%%


class CluePlayer():
    """
    A barebones Clue Player object meant to be subclassed from.

    This player makes a random guess that doesn't include the cards in its
    hand. If no-one disproves it, it makes an accusation.
    """

    def __init__(self, player_num, num_players):
        """
        Creates a player.

        :param player_num: The number for this player.
        :param num_players: The number of players in this game. This can be
            used to construct some knowledge of play.
        """
        self.cards = []
        self.player_num = player_num
        self.num_players = num_players
        self.accusation = None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(self.__dict__)

    def getCard(self, card):
        """
        Add cards to the players hand.

        :param card: The card to add.
        """
        self.cards.append(card)

    def doneSetup(self):
        """
        This will be run once all the cards have been dealt.
        """
        pass

    def makeGuess(self):
        """
        Make a guess about who dun it.

        :returns: (person, weapon, room)
        """
        # Done this way to avoid extra classes for subclassing
        person = random.choice([x for x in PEOPLE if x not in self.cards])
        weapon = random.choice([x for x in WEAPONS if x not in self.cards])
        room = random.choice([x for x in ROOMS if x not in self.cards])

        return (person, weapon, room)

    def makeAccusation(self):
        """
        Make an accusation about who dun it.

        :returns: None if not ready to make an accusation. Otherwise, return
            (person, weapon, room)
        """
        return self.accusation

    def disproveGuess(self, guess):
        """
        A basic reveal card strategy. Reveal people first, then weapons,
        then rooms.

        :param guess: The guess as a (person, weapon, room).

        :returns: The name of the card that is disproved if possible, otherwise
            None.
        """
        for g in guess:
            if g in self.cards:
                return g

        return None

    def getGuessInformation(self, player, guess, proof_list):
        """
        Get the information about the latest guess from all the players.

        :param player: The player number who made the guess.
        :param guess: The guess the player made
        :param proof_list: A list of proof. Each element is (player, proof).
            If the player was unable to disprove the accusation, then proof
            will be None. If a player was able to disprove the accusation, then
            proof will have some value. If you are the active player, it is the
            card that will disproved the accusation. Otherwise, it is
            just True.
        """
        # Check that this player guessed it and no one disproved it.
        if player == self.player_num and proof_list[-1][1] is None:
            self.accusation = guess


class ClueParticipant(CluePlayer):
    """
    A class that never makes an accusation and has no predictable strategy.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def makeAccusation(self):
        return None

    def makeGuess(self):
        person = random.choice(PEOPLE)
        weapon = random.choice(WEAPONS)
        room = random.choice(ROOMS)

        return (person, weapon, room)


class BasicCluePlayer(CluePlayer):
    """
    A basic naive clue player.

    This player randomly guesses a person, weapon and room that hasn't been
    shown to this player yet. If a guess isn't disproved, then an accusation
    is made.
    """

    def __init__(self, player_num, num_players):
        """
        Creates a player.

        :param num_players: The number of players in this game. This can be
            used to construct some knowledge of play.
        """
        super().__init__(player_num, num_players)
        # Add some basic knowledge fields
        self.remaining_people = list(PEOPLE)
        self.remaining_weapons = list(WEAPONS)
        self.remaining_rooms = list(ROOMS)

    def getCard(self, card):
        """
        Add cards to the players hand.

        :param card: The card to add.
        """
        super().getCard(card)
        self._markCardOff(card)

    def makeGuess(self):
        """
        Make a guess about who dun it.

        :returns: (person, weapon, room)
        """
        person = random.choice(self.remaining_people)
        weapon = random.choice(self.remaining_weapons)
        room = random.choice(self.remaining_rooms)

        return (person, weapon, room)

    def getGuessInformation(self, player, guess, proof_list):
        """
        Get the information about the latest guess from all the players.

        :param player: The player number who made the guess.
        :param guess: The guess the player made
        :param proof_list: A list of proof. Each element is (player, proof).
            If the player was unable to disprove the accusation, then proof
            will be None. If a player was able to disprove the accusation, then
            proof will have some value. If you are the active player, it is the
            card that will disproved the accusation. Otherwise, it is
            just True.
        """
        # Check if the last player was able to disprove this.
        if player == self.player_num:
            if proof_list[-1][1] is not None:
                self._markCardOff(proof_list[-1][1])
            else:
                self.accusation = guess

        # Check if all other possibilitites are ended.
        if len(self.remaining_people) == 1 and len(self.remaining_weapons) == 1 and len(self.remaining_rooms) == 1:
            self.accusation = (self.remaining_people[0],
                               self.remaining_weapons[0],
                               self.remaining_rooms[0])

    def _markCardOff(self, card):
        """
        Helper function for this player to remove a card that has been
        disproven.

        :param card: The card that was revealed.
        """
        # Remove the card from information we have.
        if card in self.remaining_people:
            self.remaining_people.remove(card)
        elif card in self.remaining_weapons:
            self.remaining_weapons.remove(card)
        elif card in self.remaining_rooms:
            self.remaining_rooms.remove(card)


class RecordMissesCluePlayer(CluePlayer):
    """
    After all guesses, this player will mark which cards each player did not
    have and update the probability as to where this card lies.

    This class tracks the probability that each card is in a player's hand.
    For each category (people, weapons, rooms), it guesses the card with the
    highest probability.
    """

    def __init__(self, player_num, num_players, *args, **kwargs):
        """
        Creates a new object.
        """
        super().__init__(player_num, num_players, *args, **kwargs)

        # Construct the probability table.
        # The probability for a category is (num_in_category - 1) * num_in_hand / total_number_of_cards
        # = (num_in_category - 1) / num_players
        self.probabilities = {}
        for p in PEOPLE:
            self.probabilities[p] = np.ones(num_players) / (num_players + 1)
        for w in WEAPONS:
            self.probabilities[w] = np.ones(num_players) / (num_players + 1)
        for r in ROOMS:
            self.probabilities[r] = np.ones(num_players) / (num_players + 1)

    def getCard(self, card):
        super().getCard(card)
        self._markPlayerHasCard(self.player_num, card)

    def doneSetup(self):
        """
        Run after all the cards have been dealt to indicate the round is
        about to start.
        """
        [self._markPlayerDoesNotHaveCard(self.player_num, card)
         for card in PEOPLE + WEAPONS + ROOMS if card not in self.cards]

    def _markPlayerHasCard(self, player_num, card):
        """
        Marks that a player certainly has a card.

        :param player_num: The player index.
        :param card: The card the player has.
        """

        self.probabilities[card] = np.zeros(self.num_players)
        self.probabilities[card][player_num] = 1

    def _markPlayerDoesNotHaveCard(self, player_num, card):
        """
        Marks that a player does not have a card.

        :param player_num: The player index.
        :param card: The card the player does not have.
        """
        self.probabilities[card][player_num] = 0

        self._normalizeProbabilities(card)

    def _normalizeProbabilities(self, card):
        """
        Normalize the probabilities for a card.

        :param card: The card to normalize.
        """
        # Ignore this if the card has a known location in a player's hand.
        if any(self.probabilities[card] == 1):
            return

        # Ignore this if the card isn't in anyone's hand.
        valid_hands = self.probabilities[card] > 0

        self.probabilities[card][valid_hands] = 1 / (sum(valid_hands) + 1)

    def makeGuess(self):
        """
        Chooses the cards that have the highest probability of being in the
        envelope.
        """
        person = self._guessFromList(PEOPLE)[0]
        weapon = self._guessFromList(WEAPONS)[0]
        room = self._guessFromList(ROOMS)[0]

        return (person, weapon, room)

    def _guessFromList(self, category):
        """
        Returns the card with the highest probability of being in the envelope
        given a certain category of cards.

        :param category: Either PEOPLE, WEAPONS, or ROOMS.

        :returns: (choice, probability)
        """
        highest_prob = 0
        for card in category:
            prob_in_env = 1 - sum(self.probabilities[card])
            if prob_in_env > highest_prob:
                highest_prob = prob_in_env
                winner = card

        return (winner, highest_prob)

    def getGuessInformation(self, player, guess, proof_list):
        """
        Adds the guess information to the probabilities.
        """

        # Check to see an accusation should be made
        super().getGuessInformation(player, guess, proof_list)

        # Update truth information.
        for p in proof_list:
            if p[1] is None:
                self._markPlayerDoesNotHaveCard(p[0], guess[0])
                self._markPlayerDoesNotHaveCard(p[0], guess[1])
                self._markPlayerDoesNotHaveCard(p[0], guess[2])
            elif p[1] is not True:
                self._markPlayerHasCard(p[0], p[1])

        # Check if an accusation should be made based off information update.
        guess = []
        for l in [PEOPLE, WEAPONS, ROOMS]:
            card, prob = self._guessFromList(l)
            # Need 100% certainty on all cards to guess.
            if prob != 1:
                return
            guess.append(card)

        self.accusation = tuple(guess)

#%%
if __name__ == '__main__':
    # Run a real game!
    players = [RecordMissesCluePlayer(0, 6)]
    players.extend(BasicCluePlayer(ix, 6) for ix in range(1, 6))
    cc = ClueController(players)
    print(cc.runGame())