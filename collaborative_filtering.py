import os, glob, json, re, random
from os.path import join
from math import sqrt
from pprint import pprint
from copy import deepcopy

class CollaborativeFilter():
    '''
    # def docprob(self,item,cat):
    # def prob(self,item,cat):

    # def setthreshold(self,cat,t):
    # def getthreshold(self,cat):

    # def classify(self,item,default = None):

    def sim_distance( prefs, person1, person2 ):
    def sim_pearson( prefs, p1, p2 ):

    def topMatches( prefs, person, n=5, similarity=sim_pearson ):
    def getRecommendations( prefs, person, similarity=sim_pearson ):

    def transformPrefs( prefs ):

    def calculateSimilarItems( prefs, n=10 ):
    def getRecommendedItems( prefs, itemMatch, user ):

    def loadMovieLens_data( path='./ml-100k' ):
    def loadData(path='./ml-100k'):

    def sliceData(seg_n, seg_size, reviews):

    def rmse(sum_of_squares,n):
    def k_fold_cf(subset_perc):
    '''

    ###########################################################################
    # Euclidean distance
    ###########################################################################

    # Returns a distance-based similarity score for person1 and person2
    def sim_distance( prefs, person1, person2 ):
        # Get the list of shared_items
        si={}
        for item in prefs[person1]:
          if item in prefs[person2]: si[item]=1

        # if they have no ratings in common, return 0
        if len(si)==0: return 0

        # Add up the squares of all the differences
        sum_of_squares=sum([pow(prefs[person1][item]-prefs[person2][item],2)
                            for item in prefs[person1] if item in prefs[person2]])

        return 1/(1+sum_of_squares)
    #  return 1/(1+sqrt(sum_of_squares))

    ###########################################################################
    # Pearson correlation
    ###########################################################################

    # Returns the Pearson correlation coefficient for p1 and p2
    def sim_pearson( prefs, p1, p2 ):
      # Get the list of mutually rated items
      si={}
      for item in prefs[p1]:
        if item in prefs[p2]: si[item]=1

      # if they are no ratings in common, return 0
      if len(si)==0: return 0

      # Sum calculations
      n=len(si)

      # Sums of all the preferences
      sumX=sum([prefs[p1][it] for it in si])
      sumY=sum([prefs[p2][it] for it in si])

      # Sums of the squares
      sumXSq=sum([pow(prefs[p1][it],2) for it in si])
      sumYSq=sum([pow(prefs[p2][it],2) for it in si])

      # Sum of the products
      sumXY=sum([prefs[p1][it]*prefs[p2][it] for it in si])

      # Calculate r (Pearson score)
      num=sumXY-(sumX*sumY/n)
      den=sqrt((sumXSq-pow(sumX,2)/n)*(sumYSq-pow(sumY,2)/n))
      if den==0: return 0

      r=num/den

      return r

    ###########################################################################
    # topmatches
    ###########################################################################

    # Returns the best matches for person from the prefs dictionary.
    # Number of results and similarity function are optional params.
    def topMatches( prefs, person, n=5, similarity=sim_pearson ):
      scores=[(similarity(prefs,person,other),other)
                      for other in prefs if other!=person]
      scores.sort()
      scores.reverse()
      return scores[0:n]

    ###########################################################################
    # getRecommendations
    ###########################################################################

    # Gets recommendations for a person by using a weighted average
    # of every other user's rankings
    def getRecommendations( prefs, person, similarity=sim_pearson ):
      totals={}
      simSums={}
      for other in prefs:
        # don't compare me to myself
        if other==person: continue
        sim=similarity(prefs,person,other)

        # ignore scores of zero or lower
        if sim<=0: continue
        for item in prefs[other]:

          # only score movies I haven't seen yet
          if item not in prefs[person] or prefs[person][item]==0:
            # Similarity * Score
            totals.setdefault(item,0)
            totals[item]+=prefs[other][item]*sim
            # Sum of similarities
            simSums.setdefault(item,0)
            simSums[item]+=sim

      # Create the normalized list
      rankings=[(total/simSums[item],item) for item,total in totals.items()]

      # Return the sorted list
      rankings.sort()
      rankings.reverse()
      return rankings

    ###########################################################################
    # transformPrefs
    ###########################################################################

    def transformPrefs( prefs ):
      result={}
      for person in prefs:
        for item in prefs[person]:
          result.setdefault(item,{})

          # Flip item and person
          result[item][person]=prefs[person][item]
      return result


    ###########################################################################
    # calculateSimilarItems
    ###########################################################################

    def calculateSimilarItems( prefs, n=10 ):
        # Create a dictionary of items showing which other items they
        # are most similar to.
        result={}
        # Invert the preference matrix to be item-centric
        itemPrefs = transformPrefs( prefs )
        c=0
        for item in itemPrefs:
          # Status updates for large datasets
          c+=1
          if c%100==0: print( "%d / %d" % (c,len(itemPrefs)) )
          # Find the most similar items to this one
          scores = topMatches( itemPrefs, item, n=n, similarity=sim_pearson )
          result[item] = scores
        return result

    ###########################################################################
    # getRecommendedItems
    ###########################################################################

    def getRecommendedItems( prefs, itemMatch, user ):
      userRatings=prefs[user]
      scores={}
      totalSim={}
      # Loop over items rated by this user
      for (item,rating) in userRatings.items( ):

        # Loop over items similar to this one
        for (similarity,item2) in itemMatch[item]:

          # Ignore if this user has already rated this item
          if item2 in userRatings: continue
          # Weighted sum of rating times similarity
          scores.setdefault(item2,0)
          scores[item2]+=similarity*rating
          # Sum of all the similarities
          totalSim.setdefault(item2,0)
          totalSim[item2]+=similarity

      # Divide each total score by total weighting to get an average
      rankings=[]
      for item,score in scores.items():
          total = totalSim[item]
          if total != 0:
              rankings.append((score/total,item))
          else:
              rankings.append((0,item))

      # rankings=[(score/totalSim[item],item) for item,score in scores.items( )]

      # Return the rankings from highest to lowest
      rankings.sort( )
      rankings.reverse( )
      return rankings


    ###########################################################################


    def transformToDict(votes):
        votes={}
        for vote in votes:
            congressman = vote["congressman"]
            feature = vote["feature"]
            rate = vote["vote_perc"]

            votes.setdefault( congressman, {} )
            votes[congressman][feature] = rate

        return votes


    def sliceData(seg_n, seg_size, votes):
        temp_votes = deepcopy(votes)

        start_index = seg_n*seg_size
        end_index = start_index+seg_size
        print("Segment %d (%d:%d)" % ((seg_n+1), start_index, end_index))

        if ((0<=start_index and start_index<len(temp_votes)) and
            (0<end_index and end_index<len(temp_votes)+seg_size)):
            seg = temp_votes[start_index:end_index]
            temp_votes = (temp_votes[0:start_index] +
                temp_votes[end_index:len(temp_votes)])

            prefs = transformToDict(temp_votes)

            return prefs, seg
        else:
            print(rmse_arr)
            print(start_index, end_index, len(temp_votes))
            raise IndexError('Indices out of range; segment does not exist')


    def rmse(sum_of_squares,n):
        quotient = sum_of_squares/n
        rmse = quotient**0.5

        return rmse


    def k_fold_cf(subset_perc, votes_arr):
        total_votes = len(votes_arr)
        rmse_arr = []
        item_sim = {}
        prefs = {}
        seg = []

        seg_size = int(subset_perc*total_votes)
        total_segs = int(total_votes/seg_size)

        if (total_votes%seg_size!=0):
            total_segs += 1

        for i in range(0,total_segs):
            prefs, seg = sliceData(i,seg_size,votes_arr)
            item_sim = calculateSimilarItems(prefs,n=len(prefs))

            votes = {}
            seen_votes = {}

            sumSquares = 0
            rmse_val = 0
            for vote in seg:
                congressman = vote["congressman"]
                feature = vote["feature"]

                if congressman in seen_votes:
                    votes = seen_votes[congressman]
                else:
                    votes = getRecommendedItems(prefs,item_sim,congressman)
                    seen_votes[congressman] = votes

                for (rate,subject) in votes:
                    if subject == feature:
                        predicted = rate
                        break

                actual = vote["vote_perc"]

                squaredPminusA = ((predicted - actual)**2)
                sumSquares += squaredPminusA

            rmse_val = rmse(sumSquares,len(seg))
            print("rmse = {:.5f}".format(rmse_val))
            rmse_arr.append(rmse_val)

        return rmse_arr

    print(k_fold_cf(0.1))


votesdir = '/Users/suave/mprojects/termproject/data/votes'

class MClassifier:
  def __init__(self):
    self.bills = {}
    self.votes = []
    self.congressmen = {}
    self.features = {}

class Congressman:
  def __init__(self, mID, state, party):
      # self.votes = []
      self.id = mID
      self.state = state
      self.party = party

      # Counts of feature/category combinations
      self.fc = {}
      self.prefs = {}

  def getFeatureCount(feature, clas):
      if feature in self.fc.keys():
        return self.fc[feature][clas]
      else:
        return -1

  def incrFeatureCount(feature, clas):
      self.fc.setdefault(feature, {clas:0})
      self.fc[feature][clas] += 1

      self.updatePrefs(feature, "yea")

  def updatePrefs(feature, clas):
      fcount = self.fc[feature][clas]

      total = 0
      for key in self.fc[feature].keys():
        total += self.fc[feature][key]

      self.prefs[feature] = fcount / total


def mparseFeatures(votePath=votesdir):
  congressmen = []

  with open(votePath) as vote_file:
      vote_data = json.load(vote_file)
      if("Aye" not in vote_data["votes"].keys() and
        "Yay" not in vote_data["votes"].keys()): # if it was not voted on
          return

      try: 
          bill_path = "data/bills_%d/%s/%s%d/data.json" % (
              vote_data["bill"]["congress"],
              vote_data["bill"]["type"],
              vote_data["bill"]["type"],
              vote_data["number"] )

          with open(billPath) as bill_file:
              bill_data = json.load(bill_file)
              bill = Bill(bill_data["subjects"], bill_path)

          for status in vote_data["votes"].keys():
              for vote in vote_data["votes"][status]:

                  if vote["id"] in congressmen.keys():
                      congressman = congressmen[vote["id"]]
                  else:
                      congressman = Congressman(vote["id"], vote["state"], vote["party"])
                      congressmen.append(congressman)

                  for subject in bill_data["subjects"]:
                      congressman.incrFeatureCount(subject, status)

          return congressmen

      except:
          pass

def getVotesArr(congressmen):
  votes = []

  for congressman in congressmen:
      for feature in congressman.prefs.keys():
        # v = {"congressman":congressman, "feature":feature, "vote_perc":congressman.prefs[feature]}

        v = {"congressman":congressman.id, "feature":feature, "vote_perc":congressman.prefs[feature]}
        votes.append(v)

  random.shuffle(votes)
  return votes


collab_filter = CollaborativeFilter()
congressmen = mparseFeatures()
votes_arr = getVotesArr(congressmen)
collab_filter.k_fold_cf(0.1,votes_arr)