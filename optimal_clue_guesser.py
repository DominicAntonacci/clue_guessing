#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions for the optimal clue guessing system.

The optimal clue guessing system iterates through all possible hands from
a given set of constraints and counts the number of possible hands from each
set of cards in the envelope. It will then guess the cards that are most
likely to be in the envelope (have the most possible hands from that state).

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
import copy
import itertools
import logging
import pickle

import scipy.special

from clue_guesser import PEOPLE, WEAPONS, ROOMS, CluePlayer


class MaximumLikelihoodCluePlayer(CluePlayer):
    """
    A Clue player who chooses the most likely combination of cards in the
    envelope given all the information and constraints so far.
    """

    def __init__(self, *args, **kwargs):
        """
        Creates a new object.
        """
        super().__init__(*args, **kwargs)

        if self.num_players != 6:
            raise ValueError('Cannot handle non-6 player games yet.')
        self.hand_infos = [HandInformation(3) for _ in range(self.num_players)]

        # Construct the envelope information object, which must contain one
        # person, weapon and room
        self.envelope_info = HandInformation(hand_size=3)
        self.envelope_info.addConstraint(set(PEOPLE))
        self.envelope_info.addConstraint(set(WEAPONS))
        self.envelope_info.addConstraint(set(ROOMS))

        # Save the envelope  for comparisons.
        self.envelope_counts = {}

    def getCard(self, card):
        super().getCard(card)

        self.playerHasCard(self.player_num, card)

    def playerHasCard(self, player, card):
        """
        Marks that a player has a particular card in their hand.

        :param player: The player number.
        :param card: The card they have.
        """

        for (ix, hand_info) in enumerate(self.hand_infos):
            if ix == player:
                hand_info.addKnownCard(card)
            else:
                hand_info.removePossibleCard(card)

        self.envelope_info.removePossibleCard(card)

    def playerDoesNotHaveCard(self, player, card):
        """
        Marks that a player does not have a particular card in their hand.

        :param player: The player number.
        :param card: The card the player does not have.
        """
        self.hand_infos[player].removePossibleCard(card)

    def playerHasConstraint(self, player, constraint):
        """
        Indicates that a player has a constraint on their hand.

        A constraint is defined as a set of cards that the player must have at
        least one of.

        :param player: The player number.
        :param constraint: The set of cards for the constraint.
        """
        self.hand_infos[player].addConstraint(constraint)

    def getGuessInformation(self, player, guess, proof_list):
        """
        Process the information received by someone's guess.
        """
        # Update the truth information
        for p in proof_list:
            if p[1] is None:
                for card in guess:
                    self.playerDoesNotHaveCard(p[0], card)
            elif p[1] is not True:
                # We learned a card from a particular player
                self.playerHasCard(p[0], p[1])
            else:
                # We learned that a particular player was able to disprove the
                # guess. Add a constraint.
                self.playerHasConstraint(p[0], set(guess))

        # Special case if all the players could not disprove the card.
        # In this case, if the player didn't make an accusation, then they
        # must have one of the cards.
        if all(p[1] is None for p in proof_list) and player != self.player_num:
            self.playerHasConstraint(player, guess)

        # Determine if we are ready for an accusation
        if player == self.player_num:
            self.envelope_counts = countPlayerPossibilities(self.envelope_info,
                                                            self.hand_infos)
            self.readyForAccusation()

    def makeGuess(self):
        self.envelope_counts = countPlayerPossibilities(self.envelope_info,
                                                        self.hand_infos)

        guess = max(self.envelope_counts, key=self.envelope_counts.get)
        # TODO make this less hacky. I should be able to pass sets as a guess.
        person = [x for x in guess.known_cards if x in PEOPLE][0]
        weapon = [x for x in guess.known_cards if x in WEAPONS][0]
        room = [x for x in guess.known_cards if x in ROOMS][0]
        return [person, weapon, room]

    def readyForAccusation(self):
        """
        Checks if an accusation is ready to be made.
        """
        num_nonzero_probs = 0
        best_hand = None
        for (hand, count) in self.envelope_counts.items():
            if count > 0:
                best_hand = hand
                num_nonzero_probs += 1

            # Ensure only one state is returned.
            if num_nonzero_probs > 1:
                break

        if num_nonzero_probs == 1:
            guess = best_hand
            # TODO make this less hacky. I should be able to pass sets as a guess.
            person = [x for x in guess.known_cards if x in PEOPLE][0]
            weapon = [x for x in guess.known_cards if x in WEAPONS][0]
            room = [x for x in guess.known_cards if x in ROOMS][0]
            self.accusation = [person, weapon, room]


_comb_lookup = {}


def comb(N, k):
    """
    A fast combination cacluator, using a lookup table to reuse computed
    values.

    :param N: The number of items in the full set.
    :param k: The number of items to choose per combination.

    :returns: The number of combinations.
    """
    key = (N, k)
    if key not in _comb_lookup:
        _comb_lookup[key] = scipy.special.comb(N, k, exact=True)
    return _comb_lookup[(key)]


class HandInformation:
    """
    Stores known information about a given hand and is capable of
    generating a minimal list of constraints to satisfy the hand.
    """

    def __init__(self, hand_size, known_cards=None, possible_cards=None):
        """
        Creates a new object.

        :param hand_size: The number of cards in this player's hand.
        :param known_cards: A set of cards the player is known to have.
        :param possible_cards: The set of cards the player possibly has.
            This defaults to all the cards if not specified.
        """
        self.hand_size = hand_size
        self.constraint_list = []
        if known_cards is None:
            self.known_cards = set()
        else:
            self.known_cards = known_cards

        if possible_cards is None:
            self.possible_cards = set(PEOPLE + WEAPONS + ROOMS)
        else:
            self.possible_cards = possible_cards

    def __str__(self):
        """
        Return a helpful string for the object.

        :returns: The object string.
        """
        return str(self.__dict__)

    def __repr__(self):
        """
        Modify the standard printing.
        """
        return str(self)

    @property
    def num_unknown_cards(self):
        """
        The number of unknown cards left to find in a player's hand.
        """
        return self.hand_size - len(self.known_cards)

    def addKnownCard(self, card):
        """
        Adds a known card to the player's hand.

        :param card: The card to add.
        """
        self.known_cards.add(card)
        self.removePossibleCard(card)

    def removePossibleCard(self, card):
        """
        Removes a card from the list of possible cards in the player's hand.
        """
        self.possible_cards.discard(card)

    def addConstraint(self, constraint):
        """
        Adds a constraint to the player.

        A constraint is a set of cards that the player has at least one of.
        """
        self.constraint_list.append(constraint)

    def getPossibleHands(self):
        """
        Returns all the possible hands that satisfy the constraints.

        :returns: A list of completedHandInformation objects for each hand.
        """

        hand_list = []
        for new_cards in itertools.combinations(self.possible_cards,
                                                self.num_unknown_cards):
            # Construct the new potential hand.
            hand = HandInformation(
                self.hand_size,
                known_cards=self.known_cards.union(new_cards),
                possible_cards=set())

            # Ensure it satisfies all the constraints.
            meets_constraints = True
            for constraint in self.constraint_list:
                meets_constraints &= any(c in hand.known_cards
                                         for c in constraint)

            if not meets_constraints:
                continue

            hand_list.append(hand)

        return hand_list

    def numPossibleHands(self):
        """
        Returns the number of possible hands for this object.

        :returns: The number of possible hands for this object.
        :raises ValueError: If self.constraint_list is not empty. In that case
            counting is more complex than basic combinatorics.
        """
        if len(self.constraint_list) > 0:
            raise ValueError('This method can only be called when '
                             'len(constraint_list) == 0')

        return comb(len(self.possible_cards), self.num_unknown_cards)

    def satisfyConstraints(self):
        """
        Returns a list of HandInformation objects that contain no
        constraints, but contain all the possible hands for this object.

        Each HandInforation object in the output is disjoint from all the other
        objects. That is, there will be no common hand across any of the
        HandInformation objects.

        To satisfy the disjoint property, each set of constraints will be
        broken into disjoint subsets. Thus, if the constraint is (1, 2, 3),
        the HandInformation objects will be
        [(1), (2 and not 1), (3 and not 1 and not 2)]

        If the constraints cannot be satisfied, this returns an empty list.

        There is no guarantee that the HandInformation objects will be output
        in any particular order. The current implemention may return different
        results depending on the order the constraints were added.

        :returns: A list of HandInformation objects.
        """

        # Base case: no remaining constraints, return self.
        if len(self.constraint_list) == 0:
            return [self]

        # Recursive case. Break up the next constraint.
        constraint = self.constraint_list[-1]

        # If the constraint is already satisifed, remove and try again
        if any(card in self.known_cards for card in constraint):
            hand_info = copy.deepcopy(self)
            hand_info.constraint_list.pop()
            return hand_info.satisfyConstraints()

        old_cards = []
        hand_infos = []
        for card in constraint:
            hand_info = copy.deepcopy(self)
            # Remove the last constraint from the list
            hand_info.constraint_list.pop()

            # Ensure the constraint can be satisfied.
            if card not in hand_info.known_cards and card not in hand_info.possible_cards:
                continue

            if hand_info.num_unknown_cards == 0:
                continue

            hand_info.addKnownCard(card)

            # Ensure that none of the old constraint cards are present
            # in this version
            if any(c in hand_info.known_cards for c in old_cards):
                continue

            for c in old_cards:
                hand_info.removePossibleCard(c)

            old_cards.append(card)

            # Add the new states
            hand_infos.extend(hand_info.satisfyConstraints())

        return hand_infos

    def __lt__(self, other):
        """
        Allow HandInformation objects to be ranked in a fixed format.

        This is only to facilitate sorting.
        """

        return (comb(len(self.possible_cards), self.num_unknown_cards) <
                comb(len(other.possible_cards), other.num_unknown_cards))

    def __eq__(self, other):
        """
        An equality tester for HandInformation objects. The objects are the
        same if the known cards, possible cards, and constraints are equal.
        """
        return self.__dict__ == other.__dict__

    def __hash__(self):
        """
        Required when defining __eq__. This is the default Python has function.
        """
        return id(self)


def satisfyAllConstraints(player_hands):
    """
    Generates a list of hands that satisfy all the constraints for all the
    players.

    :param player_hands: The HandInformation objects for each player.

    :returns: A list of HandInformation object lists that cover all the
        possible cases for hands.
    """

    individual_constraints = [hand.satisfyConstraints()
                              for hand in player_hands]
    hand_lists = []
    for hand_set in itertools.product(*individual_constraints):
        # Ensure no two players share a card
        all_known_cards = set()
        valid_set = True
        for hand in hand_set:
            if any(card in all_known_cards for card in hand.known_cards):
                valid_set = False
                break
            all_known_cards |= hand.known_cards

        if not valid_set:
            continue

        # Construct a new list of hands to add to the list
        hand_list = []
        for hand in hand_set:
            new_hand = copy.deepcopy(hand)
            # Remove the known cards of other hands from possibilities here.
            for other_hand in hand_set:
                if other_hand == hand:
                    continue
                for card in other_hand.known_cards:
                    new_hand.removePossibleCard(card)
            hand_list.append(new_hand)

        hand_lists.append(hand_list)

    return hand_lists


class GameStateCounter():
    """
    Counts the number of possible game states under restrictive assumptions.

    A unique game state specifies which card belongs to which player or is in
    the envelope (a kind of special player).

    This class counts the number of possible game states given a set of
    unknown cards for each player and the number of cards each player needs.
    It automatically caches previous results to speed up computation time.

    This class cannot count game states when any player still has any
    conditions that require it to have one card from a set of cards. These
    must be iteratively looped over to get the total count

    See Also: countEnvelopePossibilities
    """

    def __init__(self, cache_path='./game_state_counter_cache.pickle'):
        """
        Creates a new object.
        """
        self.logger = logging.getLogger(name=self.__class__.__name__)

        self.cache_path = cache_path
        self.loadCache()

    def loadCache(self):
        """
        Loads the cache.

        If the saved cache file cannot be found, an empty cache will be used.
        """
        self.cache = {}
        self.cache_size_on_last_load = 0

        try:
            with open(self.cache_path, 'rb') as f:
                self.cache = pickle.load(f)
                self.cache_size_on_last_load = len(self.cache)
        except FileNotFoundError:
            self.logger.info('Could not find cache %s. '
                             'Not modifying existing cache', self.cache_path)

    def saveCache(self, only_if_changed=True):
        """
        Saves the cache to a file.

        :param file_path: The path to save the cache to.
        :param only_if_changed: Only save the cache if new entries were made
            to the cache. This reduces IO when nothing has changed.
        """
        if only_if_changed and len(self.cache) == self.cache_size_on_last_load:
            self.logger.debug('Cache did not change since last load. '
                              'Not saving it')

        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache, f)

    def getCacheKey(self, hand_infos):
        """
        Computes a cache key for the given hand information.

        If any of the hand_info objects have constraints, this will return
        a ValueError.

        The cache key is an identifier for this set of hand information. It
        includes the number of unknown cards for each hand and the number
        of cards in in all the possible sets of hands.

        For example, game with players 1 and 2, the cache key will be
        (num cards in 1, num cards in 2,
         num cards not in 1 nor 2,
         num cards in 1 but not 2,
         num cards in 2 but not 1,
         num cards in 1 and 2).

        By using this numeric based structure, the number of possible cache
        keys is greatly reduced and similar sets that just exchange one card
        for another are not computed twice.

        The set size is further reduced by sorting the hand information
        objects. This removes permutation duplications.

        :param hand_infos: A list of HandInformation objects to compute the
            cache key for.

        :returns: The key to the cache for this value. If any of the hand_
        """

        # Sort arguments by hand size for a consistent ordering
        order_to_add = sorted(hand_infos)

        # Add the number of elements per set first
        key = [x.num_unknown_cards for x in order_to_add]

        # Determine the superset from all combinations. Used as a starting
        # point and will be trimmed from there.
        element_superset = set()
        for info in order_to_add:
            element_superset |= info.possible_cards

        # Add all the subset orderings
        for subset_terms in itertools.product([0, 1],
                                              repeat=len(order_to_add)):
            subset = element_superset.copy()
            for (ix, t) in enumerate(subset_terms):
                if t == 0:  # Not, so remove from subset
                    subset -= order_to_add[ix].possible_cards
                elif t == 1:  # And, so ensure in subset
                    subset &= order_to_add[ix].possible_cards
            key.append(len(subset))

        return tuple(key)

    def countPossibleStates(self, hand_infos):
        """
        Counts the number of possible hands given possible cards and a hand
        size for each player.

        This function takes an dictionary for each player. the first argument
        is a set of possible cards for that player and the second is the
        hand size for that player.

        :param comb_info: A list of CombinationInfo objects.

        :returns: The number of possible combinations of items for each
            CombinationInfo object.
        :raises ValueError: If any of the hand_info objects have constraints.
        """

        # Ensure there are no constraints remaining in hand_info. This can't
        # handle those cases (no good way to cache results).
        for h in hand_infos:
            if len(h.constraint_list) > 0:
                raise ValueError('No constraints are allowed in any element '
                                 'of hand_info.')
        # Base case
        if len(hand_infos) == 1:
            return hand_infos[0].numPossibleHands()

        # Cache case
        key = self.getCacheKey(hand_infos)
        if key in self.cache:
            return self.cache[key]

        # Recursive case. Iterate over all the possible hands for one player
        # and recursively call this function.
        # Choose the player with fewest hands to iterate over to help reduce
        # for loop iterations.
        hand_to_iterate = {'idx': 0, 'num_possible_hands': float('inf')}
        for (ix, info) in enumerate(hand_infos):
            if info.numPossibleHands() < hand_to_iterate['num_possible_hands']:
                hand_to_iterate['idx'] = ix
                hand_to_iterate['num_possible_hands'] = info.numPossibleHands()

        # For each hand in that player, recompute arguments and recurse.
        count = 0
        for hand in itertools.combinations(hand_infos[hand_to_iterate['idx']].possible_cards,
                                           hand_infos[hand_to_iterate['idx']].num_unknown_cards):
            hand_set = set(hand)
            # Construct new arguments to pass along
            new_args = []
            for (ix, info) in enumerate(hand_infos):
                if ix == hand_to_iterate['idx']:
                    continue
                new_args.append(HandInformation(
                    hand_size=info.hand_size,
                    known_cards=info.known_cards,
                    possible_cards=info.possible_cards - hand_set))
            count += self.countPossibleStates(new_args)

        # Cache the result
        self.cache[key] = count

        return count


_game_state_counter = GameStateCounter()


def countPlayerPossibilities(player_to_count, other_players):
    """
    Returns the number of possible game states for each possible hand in
    player_info.

    :param player_to_count: A HandInformation object for the player to count
        game states for (e.g. the envelope).
    :param other_players: A list of HandInformation objects for all the
        other players.

    :returns: A dictionary with each possible hand for player_info as the key
        and the value is the number of game states associated with that key.
    """
    num_possibilities = {}
    hand_lists = satisfyAllConstraints(other_players)
    for hand in player_to_count.getPossibleHands():
        num_possibilities[hand] = 0
        for hand_list in hand_lists:
            # Ensure the envelope hand doesn't conflict with the hand list
            valid_hand_list = True
            for card in hand.known_cards:
                for h in hand_list:
                    if card in h.known_cards:
                        valid_hand_list = False
                        break
            if not valid_hand_list:
                continue

            # Construct new hands and remove cards from the
            # player_to_count hand.
            new_hands = []
            for h in hand_list:
                new_hands.append(copy.deepcopy(h))
                for card in hand.known_cards:
                    new_hands[-1].removePossibleCard(card)

            num_possibilities[hand] += _game_state_counter.countPossibleStates(new_hands)

    return num_possibilities
