#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for bugs found when writing the clue guesser classes.

@author: dominic
"""
import unittest

from clue_guesser import (BasicCluePlayer,
                          CluePlayer,
                          PEOPLE,
                          RecordMissesCluePlayer,
                          ROOMS,
                          WEAPONS,
                          )

from optimal_clue_guesser import (countPlayerPossibilities,
                                  GameStateCounter,
                                  HandInformation,
                                  satisfyAllConstraints)


def assertCardConstraints(test_case, hand_info, required_cards=(),
                          missing_cards=()):
    """
    Helper function to ensure the required card constraints are satisfied.

    :param test_case: The TestCase object to push errors to.
    :param hand_info: The HandInformation object to compare with.
    :param required_cards: The cards the HandInformation object must have.
    :param missing_cards: The cards the HandInformation object must not have.
    """

    for card in required_cards:
        test_case.assertTrue(card in hand_info.known_cards,
                             msg='Card {} not in {}'.format(card, hand_info))

    for card in missing_cards:
        test_case.assertTrue(card not in hand_info.known_cards,
                             msg='Card {} incorrectly in known cards: {}'
                             .format(card, hand_info))
        test_case.assertTrue(card not in hand_info.possible_cards,
                             msg='Card {} incorrectly in possible cards: {}'
                             .format(card, hand_info))


class ForcedGuessPlayer(CluePlayer):
    """
    Always guesses the same thing; designed to remove randomness during
    testing.
    """
    def __init__(self, player_num, num_players, guess=None):
        """
        Creates a new object.

        :param guess: The guess to always make.
        """
        super().__init__(player_num, num_players)
        self.guess = guess

    def makeGuess(self):
        return self.guess


class TestBasicCluePlayer(unittest.TestCase):
    """
    Unit tests for BasicCluePlayer class.
    """
    def test_markCardOff(self):
        cp = BasicCluePlayer(1, 1)
        # Test existing person
        self.assertTrue(PEOPLE[0] in cp.remaining_people)
        cp._markCardOff(PEOPLE[0])
        self.assertFalse(PEOPLE[0] in cp.remaining_people)

        # Test existing weapon
        self.assertTrue(WEAPONS[0] in cp.remaining_weapons)
        cp._markCardOff(WEAPONS[0])
        self.assertFalse(WEAPONS[0] in cp.remaining_weapons)

        # Test existing room
        self.assertTrue(ROOMS[0] in cp.remaining_rooms)
        cp._markCardOff(ROOMS[0])
        self.assertFalse(ROOMS[0] in cp.remaining_rooms)

        # Test nothing changes
        old_people = cp.remaining_people.copy()
        old_weapons = cp.remaining_weapons.copy()
        old_rooms = cp.remaining_rooms.copy()
        cp._markCardOff(True)
        self.assertEqual(old_people, cp.remaining_people)
        self.assertEqual(old_weapons, cp.remaining_weapons)
        self.assertEqual(old_rooms, cp.remaining_rooms)

    def testGetCard(self):
        cp = BasicCluePlayer(1, 1)
        cp.getCard(PEOPLE[0])
        self.assertTrue(PEOPLE[0] not in cp.remaining_people)


class TestCluePlayer(unittest.TestCase):
    """
    Unit tests for CluePlayer class.
    """

    def testGetCard(self):
        cp = CluePlayer(1, 1)
        cp.getCard(PEOPLE[0])
        self.assertTrue(PEOPLE[0] in cp.cards)

    def testMakeGuess(self):
        cp = CluePlayer(1, 1)
        cp.getCard(PEOPLE[0])
        cp.getCard(WEAPONS[1])
        cp.getCard(ROOMS[2])
        guess = cp.makeGuess()
        self.assertTrue(guess[0] in PEOPLE)
        self.assertTrue(guess[1] in WEAPONS)
        self.assertTrue(guess[2] in ROOMS)
        for c in guess:
            self.assertTrue(c not in cp.cards)


class TestRecordMissesCluePlayer(unittest.TestCase):
    """
    Unit tests for RecordMissesCluePlayer.
    """

    def test_markPlayerHasCard(self):
        cp = RecordMissesCluePlayer(0, 3)

        cp._markPlayerHasCard(1, PEOPLE[0])

        self.assertEqual(cp.probabilities[PEOPLE[0]][0], 0)
        self.assertEqual(cp.probabilities[PEOPLE[0]][1], 1)
        self.assertEqual(cp.probabilities[PEOPLE[0]][2], 0)

    def test_markPlayerDoesNotHaveCard(self):
        cp = RecordMissesCluePlayer(0, 3)

        cp._markPlayerDoesNotHaveCard(1, PEOPLE[0])

        self.assertAlmostEqual(cp.probabilities[PEOPLE[0]][0], 1/3)
        self.assertEqual(cp.probabilities[PEOPLE[0]][1], 0)
        self.assertAlmostEqual(cp.probabilities[PEOPLE[0]][2], 1/3)

    def test_normalizeProbabilitites(self):
        cp = RecordMissesCluePlayer(0, 3)

        cp.probabilities[PEOPLE[0]][0] = 0
        cp._normalizeProbabilities(PEOPLE[0])

        self.assertEqual(cp.probabilities[PEOPLE[0]][0], 0)
        self.assertAlmostEqual(cp.probabilities[PEOPLE[0]][1], 1/3)
        self.assertAlmostEqual(cp.probabilities[PEOPLE[0]][2], 1/3)

    def test_guessFromList(self):
        cp = RecordMissesCluePlayer(0, 3)

        cp._markPlayerDoesNotHaveCard(1, PEOPLE[0])

        self.assertTrue(cp._guessFromList(PEOPLE), PEOPLE[0])

        cp._markPlayerHasCard(0, PEOPLE[0])
        self.assertTrue(cp._guessFromList(PEOPLE), PEOPLE[1])

    def test_getGuessInformationSelf(self):
        cp = RecordMissesCluePlayer(0, 6)
        player = 2
        guess = [PEOPLE[0], WEAPONS[0], ROOMS[0]]
        proof_list = [(3, None), (4, None), (5, WEAPONS[0])]

        cp.getGuessInformation(player, guess, proof_list)

        for ix in range(cp.num_players):
            for card in guess:
                if card == WEAPONS[0]:
                    if ix == 5:
                        self.assertEqual(
                            cp.probabilities[card][ix], 1,
                            msg='Player {}, card {}'.format(ix, card))
                    else:
                        self.assertEqual(
                            cp.probabilities[card][ix], 0,
                            msg='Player {}, card {}'.format(ix, card))
                elif ix == 3 or ix == 4:
                    self.assertEqual(
                        cp.probabilities[card][ix], 0,
                        msg='Player {}, card {}'.format(ix, card))
                else:
                    self.assertNotEqual(
                        cp.probabilities[card][ix], 0,
                        msg='Player {}, card {}'.format(ix, card))

    def test_getGuessInformationOthers(self):
        cp = RecordMissesCluePlayer(0, 6)
        player = 2
        guess = [PEOPLE[0], WEAPONS[0], ROOMS[0]]
        proof_list = [(3, None), (4, None), (5, True)]

        cp.getGuessInformation(player, guess, proof_list)

        for ix in range(cp.num_players):
            for card in guess:
                if ix == 3 or ix == 4:
                    self.assertEqual(
                        cp.probabilities[card][ix], 0,
                        msg='Player {}, card {}'.format(ix, card))
                else:
                    self.assertNotEqual(
                        cp.probabilities[card][ix], 0,
                        msg='Player {}, card {}'.format(ix, card))


class TestHandInformation(unittest.TestCase):
    """
    Unit Tests for HandInformation.
    """

    def testAddKnownCard(self):
        h = HandInformation(hand_size=3)
        h.addKnownCard(PEOPLE[0])

        self.assertTrue(PEOPLE[0] in h.known_cards)
        self.assertFalse(PEOPLE[0] in h.possible_cards)
        self.assertEqual(h.num_unknown_cards, 2)
        pass

    def testRemovePossibleCard(self):
        h = HandInformation(hand_size=3)
        h.removePossibleCard(PEOPLE[0])

        self.assertFalse(PEOPLE[0] in h.possible_cards)

    def testGetPossibleHandsNoConstraints(self):
        h = HandInformation(hand_size=3, possible_cards=set(PEOPLE))

        hands = h.getPossibleHands()
        # 6C3 hands will be generated.
        self.assertEqual(len(hands), 20)

        distinct_hands = set()
        for hand in hands:
            # Ensure the hand is fully populated.
            self.assertEqual(hand.num_unknown_cards, 0)
            self.assertEqual(len(hand.known_cards), hand.hand_size)

            # Ensure all the hands are unique
            self.assertTrue(hand not in distinct_hands)
            distinct_hands.add(hand)

    def testGetPossibleHandsWithConstraints(self):
        h = HandInformation(hand_size=3, possible_cards=set(PEOPLE))

        # Hand computed. This constraint will remove 4 possible cases.
        # (2,3,4), (2,3,5), (2,4,5), (3,4,5)
        constraint = set((PEOPLE[0], PEOPLE[1]))
        h.addConstraint(constraint)

        hands = h.getPossibleHands()
        self.assertEqual(len(hands), 16)

        distinct_hands = set()
        for hand in hands:
            # Ensure each hand satisfies the constraint
            self.assertTrue(any(c in hand.known_cards for c in constraint))

            # Ensure all hands are distinct
            self.assertTrue(hand not in distinct_hands)
            distinct_hands.add(hand)

        pass

    def testSatisfyConstraintsNoConstraints(self):
        # This test ensures that a hand with no constraints returns itself.

        h = HandInformation(hand_size=2)

        hands = h.satisfyConstraints()

        self.assertEqual(len(hands), 1)
        self.assertEqual(hands[0], h)

    def testSatisfyConstraintsSatisfiedConstraint(self):
        # This test ensures that a satisifed constraint is not processed.
        h = HandInformation(hand_size=2, possible_cards=set(range(6)))
        h.addKnownCard(0)
        h.addConstraint([0, 1, 2])

        hands = h.satisfyConstraints()

        self.assertEqual(len(hands), 1)
        self.assertEqual(hands[0].hand_size, h.hand_size)
        self.assertEqual(hands[0].known_cards, h.known_cards)
        self.assertEqual(hands[0].possible_cards, h.possible_cards)

    def testSatisfyConstraintsImpossibleConstraint(self):
        h = HandInformation(hand_size=1, possible_cards=set(range(6)))
        h.addKnownCard(0)
        h.addConstraint([1, 2])

        hands = h.satisfyConstraints()
        self.assertEqual(len(hands), 0)

    def testSatisfyConstraints3(self):
        h = HandInformation(hand_size=2, possible_cards=set(range(6)))
        h.addConstraint([0, 1, 2])
        h.addConstraint([0, 2, 3])

        hands = h.satisfyConstraints()
        self.assertEqual(len(hands), 3)
        # Note that hand order technically doesn't matter, but I've matched
        # the order here for ease of testing.

        # Hand 0, Card 0, all other cards allowed
        assertCardConstraints(self, hands[0], required_cards=[0])

        # Hand 1, Card 2, but no card 0
        assertCardConstraints(self, hands[1],
                              required_cards=[2],
                              missing_cards=[0])

        # Hand 2, Cards 3 and 1, but no cards 0 or 2
        assertCardConstraints(self, hands[2],
                              required_cards=[1, 3],
                              missing_cards=[0, 2])

    def testSatisfyConstraints4(self):
        h = HandInformation(hand_size=2, possible_cards=set(range(6)))
        h.addConstraint([0, 1, 2])
        h.addConstraint([0, 2, 3])
        h.addConstraint([0, 4, 5])

        hands = h.satisfyConstraints()

        self.assertEqual(len(hands), 3)
        # Hand order doesn't technically matter, but I've assumed an order.
        # Solutions computed by hand.

        # Hand 0, Card 0, all other cards allowed
        assertCardConstraints(self, hands[0], required_cards=[0])

        # Hand 1, Cards 2 and 4, but 0 not allowed
        assertCardConstraints(self, hands[1],
                              required_cards=[2, 4],
                              missing_cards=[0])

        # Hand 2, Cards 2 and 5 allowed, but 0 and 4 not allowed
        assertCardConstraints(self, hands[2],
                              required_cards=[2, 5],
                              missing_cards=[0, 4])

    def testSatisfyConstraintsCheckHands(self):
        # This test ensures that the list of possible hands match between
        # the original hand and the list of sub-hands.

        h = HandInformation(hand_size=3, possible_cards=set(range(10)))
        h.addConstraint([0, 1, 2])

        possible_hands_sol = h.getPossibleHands()

        hands = h.satisfyConstraints()
        possible_hands_test = []
        for hand in hands:
            possible_hands_test.extend(hand.getPossibleHands())

        self.assertEqual(len(possible_hands_test), len(possible_hands_sol))

        for hand in possible_hands_test:
            self.assertTrue(hand in possible_hands_sol)

    def testLessThan(self):
        h1 = HandInformation(hand_size=2)
        h2 = HandInformation(hand_size=3)
        self.assertLess(h1, h2)

    def testNumPossibleHands(self):
        h1 = HandInformation(hand_size=3, possible_cards=set(PEOPLE))
        self.assertEqual(h1.numPossibleHands(), 20)

        h1.addConstraint([set(PEOPLE[0])])
        with self.assertRaises(ValueError):
            h1.numPossibleHands()


class TestSatisfyAllConstraints(unittest.TestCase):
    """
    Unit tests for satisfyAllConstraints.
    """

    def testSinglePlayer(self):
        h = HandInformation(hand_size=3, possible_cards=set(range(6)))
        constraint1 = set((0, 1))
        h.addConstraint(constraint1)

        constraint2 = set((1, 2, 3))
        h.addConstraint(constraint2)

        hands = satisfyAllConstraints([h])

        # Hand computed solutions. Order doesn't technically matter, but I've
        # assumed the correct order.
        self.assertEqual(len(hands), 3)

        # Hand 0. Has card 1
        assertCardConstraints(self, hands[0][0],
                              required_cards=[1])

        # Hand 1. Has cards 2 and 0, but not card 1
        assertCardConstraints(self, hands[1][0],
                              required_cards=[2, 0],
                              missing_cards=[1])

        # Hand 2. Has cards 3 and 0, but not 1 or 2
        assertCardConstraints(self, hands[2][0],
                              required_cards=[3, 0],
                              missing_cards=[1, 2])

    def testNoCollisions(self):
        h1 = HandInformation(hand_size=3, possible_cards=set(range(6)))
        constraint1 = set((0, 1))
        h1.addConstraint(constraint1)

        h2 = HandInformation(hand_size=3, possible_cards=set(range(6)))
        constraint2 = set((2, 3))
        h2.addConstraint(constraint2)

        hand_lists = satisfyAllConstraints([h1, h2])

        self.assertEqual(len(hand_lists), 4)

        # Set 1. First hand 0, Second hand 2
        assertCardConstraints(self, hand_lists[0][0],
                              required_cards=[0],
                              missing_cards=[2])
        assertCardConstraints(self, hand_lists[0][1],
                              required_cards=[2],
                              missing_cards=[0])

        # Set 2. First hand 0, Second hand 3 and not 2
        assertCardConstraints(self, hand_lists[1][0],
                              required_cards=[0],
                              missing_cards=[3])
        assertCardConstraints(self, hand_lists[1][1],
                              required_cards=[3],
                              missing_cards=[0, 2])

        # Set 3. First hand 1 and not 0, Second hand 2
        assertCardConstraints(self, hand_lists[2][0],
                              required_cards=[1],
                              missing_cards=[0, 2])
        assertCardConstraints(self, hand_lists[2][1],
                              required_cards=[2],
                              missing_cards=[1])

        # Set 4. First hand 1 and not 0, Second hand 3 and not 2
        assertCardConstraints(self, hand_lists[3][0],
                              required_cards=[1],
                              missing_cards=[0, 3])
        assertCardConstraints(self, hand_lists[3][1],
                              required_cards=[3],
                              missing_cards=[1, 2])

    def testSingleCollision(self):
        h1 = HandInformation(hand_size=3, possible_cards=set(range(6)))
        constraint1 = set((0, 1))
        constraint2 = set((1, 2, 3))
        h1.addConstraint(constraint1)
        h1.addConstraint(constraint2)

        h2 = HandInformation(hand_size=3, possible_cards=set(range(6)))
        constraint3 = set([1])
        h2.addConstraint(constraint3)

        hand_lists = satisfyAllConstraints([h1, h2])

        # Hand computed solutions. As usual, the order technically doesn't
        # matter, but I've hard-coded an order for this implementation.
        self.assertEqual(len(hand_lists), 2)

        # Set 1: First hand has 0 2 and not 1, Hand 2 has 1
        assertCardConstraints(self, hand_lists[0][0],
                              required_cards=[0, 2],
                              missing_cards=[1])
        assertCardConstraints(self, hand_lists[0][1],
                              required_cards=[1],
                              missing_cards=[0, 2])

        # Set 2. First hand has 0, 3 and not 1 nor 2. Hand 2 has 1
        assertCardConstraints(self, hand_lists[1][0],
                              required_cards=[0, 3],
                              missing_cards=[1, 2])
        assertCardConstraints(self, hand_lists[1][1],
                              required_cards=[1],
                              missing_cards=[0, 3])

    def testAllCollisions(self):
        h1 = HandInformation(hand_size=3)
        constraint = set([PEOPLE[0]])
        h1.addConstraint(constraint)
        h2 = HandInformation(hand_size=3)
        h2.addConstraint(constraint)

        hand_lists = satisfyAllConstraints([h1, h2])

        self.assertEqual(len(hand_lists), 0)

    def testNoConstraints(self):
        h1 = HandInformation(hand_size=3)
        h2 = HandInformation(hand_size=3)

        hand_lists = satisfyAllConstraints([h1, h2])

        self.assertEqual(len(hand_lists), 1)
        self.assertEqual(hand_lists[0][0], h1)
        self.assertEqual(hand_lists[0][1], h2)

    def testComplexSet(self):
        # A more complex scenario with some overlap.
        h1 = HandInformation(hand_size=3, possible_cards=set(range(6)))
        h1.addConstraint(set((0, 1, 2)))
        h2 = HandInformation(hand_size=3, possible_cards=set(range(1, 8)))
        h2.addConstraint(set((1, 2, 3)))

        hand_lists = satisfyAllConstraints([h1, h2])

        self.assertEqual(len(hand_lists), 7)

        # Set 1: First hand 0, second hand 1
        assertCardConstraints(self, hand_lists[0][0],
                              required_cards=[0],
                              missing_cards=[1])
        assertCardConstraints(self, hand_lists[0][1],
                              required_cards=[1],
                              missing_cards=[0])

        # Set 2: First hand 0, second hand 2 and not 1
        assertCardConstraints(self, hand_lists[1][0],
                              required_cards=[0],
                              missing_cards=[2])
        assertCardConstraints(self, hand_lists[1][1],
                              required_cards=[2],
                              missing_cards=[0, 1])

        # Set 3: First hand 0, second hand 3 and not 1 nor 2
        assertCardConstraints(self, hand_lists[2][0],
                              required_cards=[0],
                              missing_cards=[3])
        assertCardConstraints(self, hand_lists[2][1],
                              required_cards=[3],
                              missing_cards=[0, 1, 2])

        # Set 4: First hand 1 and not 0, second hand 2 and not 1
        assertCardConstraints(self, hand_lists[3][0],
                              required_cards=[1],
                              missing_cards=[0, 2])
        assertCardConstraints(self, hand_lists[3][1],
                              required_cards=[2],
                              missing_cards=[1])

        # Set 5: First hand 1 and not 0, second hand 3 and not 2 nor 1
        assertCardConstraints(self, hand_lists[4][0],
                              required_cards=[1],
                              missing_cards=[3])
        assertCardConstraints(self, hand_lists[4][1],
                              required_cards=[3],
                              missing_cards=[1, 2])

        # Set 6: First hand 2 and not 1 nor 0, second hand 1
        assertCardConstraints(self, hand_lists[5][0],
                              required_cards=[2],
                              missing_cards=[0, 1])
        assertCardConstraints(self, hand_lists[5][1],
                              required_cards=[1],
                              missing_cards=[2])

        # Set 7: First hand 2 and not 0 nor 1, second hand 3 and not 1 nor 2
        assertCardConstraints(self, hand_lists[6][0],
                              required_cards=[2],
                              missing_cards=[0, 1, 3])
        assertCardConstraints(self, hand_lists[6][1],
                              required_cards=[3],
                              missing_cards=[1, 2])


class TestGameStateCounter(unittest.TestCase):
    """
    Unit tests for GameStateCounter.
    """

    def testGetCacheKey1Person(self):
        gsc = GameStateCounter(cache_path='')

        h = HandInformation(hand_size=3, possible_cards=set(range(6)))

        key = gsc.getCacheKey([h])
        self.assertEqual(key, (3, 0, 6))

    def testGetCacheKey2People(self):
        gsc = GameStateCounter(cache_path='')

        h1 = HandInformation(hand_size=3,
                             possible_cards=set([1, 2, 3, 4, 5, 6]))
        h2 = HandInformation(hand_size=3,
                             possible_cards=set([3, 4, 5, 6, 7, 8]))

        key = gsc.getCacheKey([h1, h2])
        self.assertEqual(key, (3, 3, 0, 2, 2, 4))

    def testGetCacheKey3People(self):
        gsc = GameStateCounter(cache_path='')

        # This is the order they are sorted in.
        h3 = HandInformation(hand_size=1,
                             possible_cards=set([6, 7, 10]))
        h1 = HandInformation(hand_size=3,
                             possible_cards=set([1, 2, 3, 4, 5, 6]))
        h2 = HandInformation(hand_size=3,
                             possible_cards=set([3, 4, 5, 6, 7, 8]))

        key = gsc.getCacheKey([h1, h2, h3])
        self.assertEqual(key, (1, 3, 3, 0, 1, 2, 3, 1, 1, 0, 1))

    def testCountPossibleCombsBaseCase(self):
        gsc = GameStateCounter(cache_path='')
        h = HandInformation(hand_size=3, possible_cards=set(range(6)))

        self.assertEqual(gsc.countPossibleStates([h]), 20)

    def testCountPossibleCombsDisjointSets(self):
        """
        Disjoint sets should simply multiply, making computation of
        answers easy
        """
        gsc = GameStateCounter(cache_path='')

        h1 = HandInformation(hand_size=3,
                             possible_cards=set([1, 2, 3, 4, 5, 6]))
        h2 = HandInformation(hand_size=2,
                             possible_cards=set([7, 8, 9]))
        h3 = HandInformation(hand_size=1,
                             possible_cards=set([10, 11, 12, 13, 14]))

        possible_hands = gsc.countPossibleStates([h1, h2, h3])
        self.assertEqual(possible_hands, 20*3*5)

    def testCountPossibleCombsOverlappingSets(self):
        gsc = GameStateCounter(cache_path='')

        h1 = HandInformation(hand_size=3,
                             possible_cards=set([1, 2, 3, 4, 5, 6]))
        h2 = HandInformation(hand_size=3,
                             possible_cards=set([3, 4, 5, 6, 7, 8]))

        possible_hands = gsc.countPossibleStates([h1, h2])

        # Solution computed by hand.
        # There are 4 hands where 1 card from player 1 overlaps with player 2.
        # This corresponds to 4*5C3
        # There are 12 hands where 2 cards from player 1 overlap with player 2.
        # This corresponds with 12*4C3
        # There are 4 hands where 3 cards from player 1 overlap with player 2.
        # This corresponds to 4*3C3.
        # In total, its 4*5C3 + 12*4C3 + 4*3C3 = 92
        self.assertEqual(possible_hands, 92)


class TestCountPlayerPossibilities(unittest.TestCase):
    """
    Unit tests for countPlayerPossibilities.
    """

    def testSimpleCase(self):
        player_to_count = HandInformation(
                hand_size=3, possible_cards=set([1, 2, 3, 4, 5, 6]))

        # One case to satisfy both players
        p1 = HandInformation(hand_size=1, possible_cards=set([7]))
        p2 = HandInformation(hand_size=1, possible_cards=set([8, 9, 10]))
        p2.addConstraint(set([6, 7, 8]))

        poss = countPlayerPossibilities(player_to_count, [p1, p2])

        self.assertEqual(len(poss), 20)
        for hand, count in poss.items():
            self.assertEqual(count, 1)

    def testSingleConstraint(self):
        player_to_count = HandInformation(
                hand_size=3, possible_cards=set([1, 2, 3, 4, 5]))

        p1 = HandInformation(hand_size=2, possible_cards=set([1, 2, 3, 7]))
        p1.addConstraint(set([1, 2, 3]))

        poss = countPlayerPossibilities(player_to_count, [p1])

        # Hand computed solution
        for key, count in poss.items():
            if key.known_cards in [set((1, 2, 3))]:
                self.assertEqual(count, 0)
            if key.known_cards in [set((1, 2, 4)),
                                   set((1, 2, 5)),
                                   set((1, 3, 4)),
                                   set((1, 3, 5)),
                                   set((2, 3, 4)),
                                   set((2, 3, 5))]:
                self.assertEqual(count, 1)
            if key.known_cards in [set((1, 4, 5)),
                                   set((2, 4, 5)),
                                   set((3, 4, 5))]:
                self.assertEqual(count, 3)

    def testMultipleConstraints(self):
        # A complex scenario involving 2 players. Solutions were hand computed
        # with much effort.

        h1 = HandInformation(hand_size=3, possible_cards=set(range(6)))
        h1.addConstraint(set((0, 1, 2)))
        h2 = HandInformation(hand_size=2, possible_cards=set(range(1, 8)))
        h2.addConstraint(set((1, 2, 3)))

        env = HandInformation(hand_size=3, possible_cards=set(range(8)))

        poss = countPlayerPossibilities(env, [h1, h2])

        self.assertEqual(len(poss), 56)

        for key, count in poss.items():
            # Count == 0
            if key.known_cards in [set((0, 1, 2)),
                                   set((0, 1, 3)),
                                   set((0, 1, 4)),
                                   set((0, 1, 5)),
                                   set((0, 2, 3)),
                                   set((0, 2, 4)),
                                   set((0, 2, 5)),
                                   set((0, 3, 4)),
                                   set((0, 3, 5)),
                                   set((0, 4, 5)),
                                   set((1, 2, 3)),
                                   set((1, 2, 4)),
                                   set((1, 2, 5)),
                                   set((1, 3, 4)),
                                   set((1, 3, 5)),
                                   set((1, 4, 5)),
                                   set((2, 3, 4)),
                                   set((2, 3, 5)),
                                   set((2, 4, 5)),
                                   set((3, 4, 5))]:
                self.assertEqual(count, 0,
                                 msg='Expected 0 game states from Hand {} '
                                 '(had {} game states)'
                                 .format(key.known_cards, count))
            # Count == 1
            elif key.known_cards in [set((0, 1, 6)),
                                     set((0, 1, 7)),
                                     set((0, 2, 6)),
                                     set((0, 2, 7)),
                                     set((1, 2, 6)),
                                     set((1, 2, 7)),
                                     set((1, 3, 6)),
                                     set((1, 3, 7)),
                                     set((2, 3, 6)),
                                     set((2, 3, 7))]:
                self.assertEqual(count, 1,
                                 msg='Expected 1 game state from Hand {} '
                                 '(had {} game states)'
                                 .format(key.known_cards, count))
            # Count == 2
            elif key.known_cards in [set((0, 3, 6)),
                                     set((0, 3, 7)),
                                     set((1, 4, 6)),
                                     set((1, 4, 7)),
                                     set((1, 5, 6)),
                                     set((1, 5, 7)),
                                     set((2, 4, 6)),
                                     set((2, 4, 7)),
                                     set((2, 5, 6)),
                                     set((2, 5, 7)),
                                     set((3, 4, 6)),
                                     set((3, 4, 7)),
                                     set((3, 5, 6)),
                                     set((3, 5, 7))]:
                self.assertEqual(count, 2,
                                 msg='Expected 2 game states from Hand {} '
                                 '(had {} game states)'
                                 .format(key.known_cards, count))
            # Count == 3
            elif key.known_cards in [set((0, 4, 6)),
                                     set((0, 4, 7)),
                                     set((0, 5, 6)),
                                     set((0, 5, 7)),
                                     set((4, 5, 6)),
                                     set((4, 5, 7))]:
                self.assertEqual(count, 3,
                                 msg='Expected 3 game states from Hand {} '
                                 '(had {} game states)'
                                 .format(key.known_cards, count))
            # Count == 5
            elif key.known_cards in [set((1, 6, 7)),
                                     set((2, 6, 7)),
                                     set((3, 6, 7))]:
                self.assertEqual(count, 5,
                                 msg='Expected 5 game states from Hand {} '
                                 '(had {} game states)'
                                 .format(key.known_cards, count))
            # Count == 6
            elif key.known_cards in [set((4, 6, 7)),
                                     set((5, 6, 7))]:
                self.assertEqual(count, 6,
                                 msg='Expected 6 game states from Hand {} '
                                 '(had {} game states)'
                                 .format(key.known_cards, count))
            # Count == 8
            elif key.known_cards in [set((0, 6, 7))]:
                self.assertEqual(count, 8,
                                 msg='Expected 8 game states from Hand {} '
                                 '(had {} game states)'
                                 .format(key.known_cards, count))
            else:
                self.fail(msg='Missing solution for Hand {}'
                          .format(key.known_cards))


if __name__ == '__main__':
    unittest.main()
