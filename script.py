import sys
import math
import copy
import time
import random

ABILITIES_ADD = [0.2, 0, 0.3, 0.3, 0.3, 0.4]
ABILITIES_ADD_TAKE = [0.1, 0.3, 0.2, 0.5, 0.5, 0.3]
MAXCOMP = 0.09
MAXSTATES = 10000

StartT = 0
EndRec = False

NUMM = 0

def getCard():
    x = input()
    card_number, instance_id, location, card_type, cost, attack, defense, abilities, my_health_change, opponent_health_change, card_draw = x.split()
    return(Card(int(card_number), int(instance_id), int(location), int(cost), int(attack), int(defense), abilities, int(my_health_change), int(opponent_health_change), int(card_type), int(card_draw)))


class Card:
    def __init__(self, ident, inst, location, cost, attack, defense, abilities, my_health_change, opponent_health_change, typ, card_draw):
        self.ident = ident
        self.inst = inst
        self.location = location
        self.cost = cost
        self.attack = attack
        self.defense = defense
        self.abilities = list(range(6))
        self.abilities[0] = "B" in abilities
        self.abilities[1] = "C" in abilities
        self.abilities[2] = "D" in abilities
        self.abilities[3] = "G" in abilities
        self.abilities[4] = "L" in abilities
        self.abilities[5] = "W" in abilities
        self.my_health_change = my_health_change
        self.opponent_health_change = opponent_health_change
        self.typ = typ
        self.card_draw = card_draw
        self.canAttack = False

    def value(self):
        mul = 1
        for i in range(6):
            if(self.abilities[i]):
                mul+=ABILITIES_ADD[i]
        return(self.defense + self.attack)*mul

    def printDebug(self):
        print("Card: " + str(self.inst), file=sys.stderr)

    def takeValue(self):
        if self.typ == 2 or self.typ == 3:
            return 1
        if self.cost == 0 or self.attack ==1:
            return 1

        return (self.attack *1.5 +self.defense)/self.cost +self.abilities.count(True)


    #def tacticValue(self):
    #    if(self.ident in BEST_CARDS):
    #       return 5
    #    else:
    #        return self.takeValue()/10


class Player:
    def __init__(self, health, mana, deck):
        self.health = health
        self.mana = mana
        self.deck = deck

################################################################################ GAME STATE ##############################################################

class GameState:

    def __init__(self):
        self.myReadyCreatures = []
        self.myNonReadyCreatures = []
        self.enymyCreatures = []
        self.myCards = []
        self.players = {}
        self.possibilities = []
        self.canSummon = True

    def init(self, players, cardCount):

        self.players = players
        for i in range(cardCount):
            self.addCard()
        self.getPossibilities()

    def addCard(self):
        c = getCard()
        if(c.location == 1):
            self.myReadyCreatures.append(c)
        elif(c.location == -1):
            self.enymyCreatures.append(c)
        else:
            self.myCards.append(c)

    def getPossibilities(self):
        if(self.canSummon):
            self.getCards()
        if(self.canSummon == False):
            self.getAttacks()

    def getCards(self):
        for c in self.myCards:
            if(c.cost <= self.players["me"].mana):
                if(c.typ == 0):
                    self.possibilities.append(OneMove("SUMMON", c.inst, -1))
                elif(c.typ == 3):
                    self.possibilities.append(OneMove("USE", c.inst, -1))
                elif(c.typ == 1 and (len(self.myReadyCreatures) + len(self.myNonReadyCreatures)) != 0):
                    for creat in self.myNonReadyCreatures:
                        self.possibilities.append(OneMove("USE", c.inst, creat.inst))
                    for creat in self.myReadyCreatures:
                        self.possibilities.append(OneMove("USE", c.inst, creat.inst))
                elif(c.typ == 2 and len(self.enymyCreatures) != 0):
                    for creat in self.enymyCreatures:
                        self.possibilities.append(OneMove("USE", c.inst,  self.enymyCreatures[0].inst))
        if(len(self.possibilities) == 0):
            self.canSummon = False

    def getAttacks(self):
        tar = []
        canAttackHead = True
        for c in self.enymyCreatures:
            if (c.abilities[3]):
                canAttackHead = False
                break

        if(canAttackHead):
             for c in self.enymyCreatures:
                 tar.append(c)
        else:
            for c in self.enymyCreatures:
                if(c.abilities[3]):
                    tar.append(c)

        for mcreat in self.myReadyCreatures:
            for ecreat in tar:
                self.possibilities.append(OneMove("ATTACK", mcreat.inst, ecreat.inst))
            if(canAttackHead):
                self.possibilities.append(OneMove("ATTACK", mcreat.inst, -1))
            else:
                self.possibilities.append(OneMove("---",mcreat.inst,-1))

    ######end of init functions ############################## Start of play functions

    def play(self, m):
        res = GameState()
        res.myReadyCreatures = copy.deepcopy(self.myReadyCreatures)
        res.myNonReadyCreatures = copy.deepcopy(self.myNonReadyCreatures)
        res.enymyCreatures = copy.deepcopy(self.enymyCreatures)
        res.myCards = copy.deepcopy(self.myCards)
        res.players = copy.deepcopy(self.players)
        res.possibilities = []
        res.canSummon = True

        if(m.cat == "SUMMON"):
            res.playSummon(m)
        elif(m.cat == "USE"):
            res.playUse(m)
        elif(m.cat == "ATTACK"):
            res.playAttack(m)
        elif(m.cat == "---"):
            res.play_n(m)

        res.getPossibilities()
        return res

    def reversePlayers(self):
        res = GameState()
        res.myReadyCreatures = copy.deepcopy(self.enymyCreatures)
        res.myNonReadyCreatures = []
        res.enymyCreatures = copy.deepcopy(self.myNonReadyCreatures)
        res.myCards = []
        res.players = copy.deepcopy(self.players)
        pom = res.players["me"]
        res.players["me"] = res.players["enymy"]
        res.players["enymy"] = pom
        res.possibilities = []
        res.canSummon = False

        res.getPossibilities()
        return res


    def playSummon(self,m):
        card = None
        for c in self.myCards:
            if(c.inst == m.cInst):
                card = c
        self.players["me"].health += card.my_health_change
        self.players["enymy"].health += card.opponent_health_change
        self.players["me"].mana -= card.cost
        self.myCards.remove(card)
        if(card.typ == 0):
            if(card.abilities[1]):
                self.myReadyCreatures.append(card)
            else:
                self.myNonReadyCreatures.append(card)

    def playUse(self, m):
        card = None
        for c in self.myCards:
            if(c.inst == m.cInst):
                card = c
        self.players["me"].health += card.my_health_change
        self.players["enymy"].health += card.opponent_health_change
        self.players["me"].mana -= card.cost
        self.myCards.remove(card)
        if(card.typ == 1):
            tar = None
            for c in self.myReadyCreatures:
                if(c.inst == m.target):
                    tar = c
            if(tar == None):
                for c in self.myNonReadyCreatures:
                    if(c.inst == m.target):
                        tar = c
            for i in range(6):
                if(card.abilities[i]):
                    tar.abilities[i] = True
            if(card.abilities[1] and tar.abilities[1] == False):
                self.myNonReadyCreatures.remove(tar)
                self.myReadyCreatures.append(tar)
            tar.defense += card.defense
            tar.attack += card.attack
        if(card.typ == 2):
            tar = None
            for c in self.enymyCreatures:
                if(c.inst == m.target):
                    tar = c
            if(tar == None):
                for c in self.myNonReadyCreatures:
                    if(c.inst == m.target):
                        tar = c
            for i in range(6):
                if(card.abilities[i]):
                    tar.abilities[i] = False
            tar.defense += card.defense
            tar.attack += card.attack
            if(tar.defense < 0):
                self.enymyCreatures.remove(tar)
        if(card.typ == 3):
            pass

    def playAttack(self, m):
        card = None
        for c in self.myReadyCreatures:
            if(c.inst == m.cInst):
                card = c
        if(m.target == -1):
            self.players["enymy"].health -= card.attack
            if(card.abilities[2]):
                self.players["me"].health += card.attack
        else:
            tar = None
            for c in self.enymyCreatures:
                if(c.inst == m.target):
                    tar = c
            if(tar.abilities[5]):
                card.defense -= tar.attack
                if(card.attack > 0):
                    tar.abilities[5] = False
                if(card.abilities[5]):
                    card.defense += tar.attack
                    card.abilities[5] = False

            elif(tar.abilities[4]):
                card.defense -= 1000
                tar.defense -= card.attack

                if(card.abilities[0]):
                    if(card.attack > tar.defense):
                        self.players["me"].health += card.attack - tar.defense
                if(card.abilities[2]):
                    if(tar.defense > 0):
                        self.players["me"].health += card.attack
                    else:
                        self.players["me"].health += tar.defense + card.attack
                if(card.abilities[4]):
                    tar.defense = 0
                if(card.abilities[5]):
                    card.defense += 1000
                    card.abilities[5] = False

            else:
                tar.defense -= card.attack
                card.defense -= tar.attack
                if(card.abilities[0]):
                    if(card.attack > tar.defense):
                        self.players["me"].health += card.attack - tar.defense
                if(card.abilities[2]):
                    if(tar.defense > 0):
                        self.players["me"].health += card.attack
                    else:
                        self.players["me"].health += tar.defense + card.attack
                if(card.abilities[4]):
                    tar.defense = 0
                if(card.abilities[5]):
                    card.defense += tar.attack
                    card.abilities[5] = False

            if(tar.defense <= 0):
                self.enymyCreatures.remove(tar)

        self.myReadyCreatures.remove(card)
        self.myNonReadyCreatures.append(card)
        if(card.defense <= 0):
            self.myNonReadyCreatures.remove(card)

    def play_n(self, m):
        card = None
        for c in self.myReadyCreatures:
            if(c.inst == m.cInst):
                card = c
        self.myReadyCreatures.remove(card)
        self.myNonReadyCreatures.append(card)


################ end of plays functions ################ start value function

    def getValue(self):
        global NUMM
        NUMM += 1
        if(self.players["enymy"].health <= 0):
            return 777777
        elif(self.players["me"].health <= 0):
            return -777777
        else:
            res = 0
            res += (self.players["me"].health)*0.7
            res -= (self.players["enymy"].health)*0.1
            for c in self.myNonReadyCreatures:
                res += c.value()
            for c in self.myReadyCreatures:
                res += c.value() * 1
            for c in self.enymyCreatures:
                res -= c.value() * 1.3

        return res

    def getHash(self):
        res = 0
        res += (self.players["me"].health)*100
        res -= (self.players["enymy"].health)
        for c in self.myNonReadyCreatures:
            res += c.value()
        for c in self.myReadyCreatures:
            res += c.value() * 1
        for c in self.enymyCreatures:
            res -= c.value() * 1.4

        return res

#################################################################################################    MOVE   ################################################################################

class OneMove:
    def __init__(self, cat, x, y):
        self.cat = cat
        self.cInst = x
        self.target = y

    def printMe(self):
        if(self.cat == "SUMMON"):
            return(self.cat+" "+str(self.cInst))
        elif(self.cat == "---"):
            return ""
        else:
            return(self.cat+" "+str(self.cInst)+" "+str(self.target))
    def printDebug(self):
        print(self.cat+" "+str(self.cInst)+" "+str(self.target), file=sys.stderr)


##################################################################################################   NODE    #########################################################################

class Node:

    def __init__(self, state, enymyState):

        self.state = state
        self.value = self.state.getValue()
        self.stateHash = self.state.getHash()
        self.possibilitiesNum = len(state.possibilities)

        self.enymyState = enymyState

        self.moves = []
        self.childrens = []
        self.greatParent = None

    def createAllChildren(self):
        if(self.possibilitiesNum != 0):
            for move in self.state.possibilities:
                self.createChild(move)

    def createChild(self, move):
        n = Node(self.state.play(move), self.enymyState)
        if(n.enymyState == False):
            n.moves = copy.deepcopy(self.moves)
            n.moves.append(copy.deepcopy(move))
        else:
            n.greatParent = self.greatParent
        self.childrens.append(n)

    def createBadChild(self):
        n = Node(self.state.reversePlayers(), True)
        n.greatParent = self
        self.childrens.append(n)

####################################################################################### TREE  ###########################################################

class Tree:

    def __init__(self, players, cardCount):
        gs = GameState()
        gs.init(players, card_count)
        self.firstNode = Node(gs, False)
        self.lastNodes = []
        self.wasValues = []

    def buildTree(self, node):
        print(node.value, file=sys.stderr)
        node.createAllChildren()
        for n in node.childrens:     
            checkTime()
            if(EndRec):
                print("No time", file=sys.stderr)
                return
            if(n.possibilitiesNum == 0):
                self.lastNodes.append(n)
            else:
                if(n.value not in self.wasValues):
                    self.wasValues.append(n.value)
                    self.buildTree(n)

    def buildAll(self):
        self.buildTree(self.firstNode)

    def bestNode(self):
        if(self.lastNodes):
            return max(self.lastNodes, key = lambda x:x.value)
        else:
            return self.firstNode


######################################################################################    MAIN FUNCTIONS     ######################################################################

def playRound(players, cardCount):
    tree = Tree(players, cardCount)
    tree.buildAll()
    node = tree.bestNode()
    moves = node.moves

    for k in moves:
        k.printDebug()

    if(len(moves) == 0):
        print("PASS")
    else:
        text = ""
        for i in moves:
            text+=i.printMe()
            text+=";"
        print (text)

def draftCard(cardCount):
    car = []
    for i in range(cardCount):
        car.append(getCard())
    print("PICK", car.index(max(car, key = lambda x: x.takeValue())))


def checkTime():
    global EndRec
    now = time.time()
    if(now - StartT >= MAXCOMP):
        EndRec = True

##########################################################################################   MAIN LOOP     #####################################################################################
while True:
    NUMM = 0
    state = "Draft"
    players = {}
    for i in range(2):
        player_health, player_mana, player_deck, player_rune, player_draw = [int(j) for j in input().split()]
        if(i == 0):
            players["me"] = Player(player_health, player_mana, player_deck)
        else:
            players["enymy"] = Player(player_health, player_mana, player_deck)

        if(player_mana == 0):
            state = "Draft"
        elif(player_mana != 0):
            state = "Game"


    opponent_hand, opponent_actions = [int(i) for i in input().split()]

    for i in range(opponent_actions):
        card_number_and_action = input()

    card_count = int(input())

    if(state == "Draft"):
        draftCard(card_count)
    else:
        StartT = time.time()
        EndRec = False
        playRound(players, card_count)

    print("NUM:",NUMM , file=sys.stderr)


#  To debug: print("Debug messages...", file=sys.stderr)

