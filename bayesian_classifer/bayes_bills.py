import sys, time, math, os, json, pickle
from pprint import pprint

class classifier:
    def __init__(self, getfeatures, filename=None):
        # Counts of feature/category combinations
        self.fc = {}
        # Counts of documents in each category
        self.cc = {}
        self.getfeatures = getfeatures
      
    # Increase the count of a feature/category pair
    def incf(self,f,cat):
        self.fc.setdefault(f,{})
        self.fc[f].setdefault(cat,0)
        self.fc[f][cat]+=1

    # Increase the count of a category
    def incc(self,cat):
        self.cc.setdefault(cat,0)
        self.cc[cat]+=1

    # The number of times a feature has appeared in a category
    def fcount(self,f,cat):
        if f in self.fc and cat in self.fc[f]: 
            return float(self.fc[f][cat])
        return 0.0

    # The number of items in a category
    def catcount(self,cat):
        if cat in self.cc:
            return float(self.cc[cat])
        return 0

    # The total number of items
    def totalcount(self):
        return sum(self.cc.values())

    # The list of all categories
    def categories(self):
        return self.cc.keys()

    def train(self,item):
        features, cat = self.getfeatures(item)
        # Increment the count for every feature with this category
        for f in features:
            self.incf(f,cat)

      # Increment the count for this category
        self.incc(cat)

    def fprob(self,f,cat):
        if self.catcount(cat)==0: return 0

      # The total number of times this feature appeared in this 
      # category divided by the total number of items in this category
        return self.fcount(f,cat)/self.catcount(cat)

    def weightedprob(self,f,cat,prf,weight=1.0,ap=0.5):
        # Calculate current probability
        basicprob=prf(f,cat)

        # Count the number of times this feature has appeared in
        # all categories
        totals=sum([self.fcount(f,c) for c in self.categories()])

        # Calculate the weighted average
        bp=((weight*ap)+(totals*basicprob))/(weight+totals)
        return bp

class naivebayes(classifier):
    def __init__(self,getfeatures):
        classifier.__init__(self, getfeatures)
        self.thresholds={}

    def docprob(self,item,cat):
        features = self.getfeatures(item)[0]

        # Multiply the probabilities of all the features together
        p = 1
        for f in features: p += math.log(self.weightedprob(f,cat,self.fprob))
        return -1*p

    def prob(self,item,cat):
        catprob = self.catcount(cat)/self.totalcount()
        docprob = self.docprob(item,cat)
        return 100.0 - (docprob * catprob)

    def setthreshold(self,cat,t):
        self.thresholds[cat]=t

    def getthreshold(self,cat):
        if cat not in self.thresholds: return 1.0
        return self.thresholds[cat]

    def classify(self,item,default = None):
        probs={}
        # Find the category with the highest probability

        max = 0.0
        best = 0
        for cat in self.categories():
          probs[cat] = self.prob(item,cat)
          if probs[cat] > max: 
            max = probs[cat]
            best = cat
        for cat in probs:
          if cat==best: continue
          if probs[cat]*self.getthreshold(best)>probs[best]: return default
        return 1 - best

# because there are too many bill_statuses to be useful, we will group them into XXX categories:
# 1. became law
# 2. passed in second branch
# 3. passed in first branch
# 4. brought to a vote
# 5. not brought to a vote
def process_states(status): pass # implementation reduced accuracy to worse than guessing

def process_states_simple(status):
    return 1 if "ENACTED" in status else 0

# takes a path to a bill and creates a dictionary that maps a feature to it's value
# in this case we are just going to map a feature to it's status
def getBillFeatures(billPath):
    feature_dict = {}
    status = ""
    with open(billPath) as data_file:
        data = json.load(data_file)

        try:
            # feature_dict[data["bill_id"]] = data["subjects"] + [data["status"]]
            status = process_states_simple(data["status"])

            for subject in data["subjects"]:
                feature_dict[subject] = status
            # # feature_dict[data["bill_type"]] = status
            feature_dict[data["sponsor"]["name"]] = status
        except: pass

    return feature_dict, status

def trainForCongress(predictor, billPath):
    file_count = 0
    for path, dirs, files in os.walk(billPath):
        file_count += len(files)
    i = 0
    for path, dirs, files in os.walk(billPath):
        # file_count = len(dirs) * len(files)
        for data_file in files:
            if ".json" in data_file:
            # we only want to read the .json files because we don't want to read the same data twice
                predictor.train(path + "/" + data_file)

                sys.stdout.flush()
                sys.stdout.write("\r\t\ttrained %d/%d bills... " % (i + 1, file_count))
            i += 1
    print("finished %s" % billPath)

def trainFeatureDict(predictor):
    print("\tTraining classifier...")
    trainForCongress(predictor, "data/bills_111")
    trainForCongress(predictor, "data/bills_112")
    print("\t\t--> done training!")

def predictOutcomes(predictor):
    print("Predicting Outcomes for 113th congress...")
    outcomes = [0,0]
    bill_count = 0
    for path, dirs, files in os.walk("data/bills_113"):
        bill_count += len(files)
    bill = 0
    for path, dirs, files in os.walk("data/bills_113"):
        for data_file in files:
            bill += 1

            actual = predictor.getfeatures(path + "/" + data_file)[1]
            predicted = predictor.classify(path + "/" + data_file)

            outcomes[0] += 1 if (actual == predicted) else 0
            outcomes[1] += 1

            sys.stdout.flush()
            sys.stdout.write("\r\tclassified bill %d/%d..." % (bill, bill_count))
    
    print("Done!\n")
    print("Accuracy --> %.5f%% for %d bills" % (100*outcomes[0]/outcomes[1], outcomes[1]))

def main():
    if not os.path.exists("data"):
        message = """\t 
            You don't have the data/ folder with the JSON versions of each bill.
            please run the following command to download them (takes ~15 depending on the computer)

            ./helpers/download_files.sh <congress-number>

        """
        print(message)

        return

    start = time.time()
    congressional_predictor = "maybe?"
    print("Creating Classifier...")

    if not os.path.isfile("predictor.bayes"):
        print("\tGenerating...")
        congressional_predictor = naivebayes(getBillFeatures)
        trainFeatureDict(congressional_predictor)

        save_file = open("predictor.bayes", "wb+")
        pickle.dump(congressional_predictor, save_file)
    else:
        print("\tLoaded from file")
        save_file = open("predictor.bayes", "rb")
        congressional_predictor = pickle.load(save_file)

    predictOutcomes(congressional_predictor)
    totalTime = time.time() - start
    message = "\nTime for this run: " + ("%2d:%2d" % (totalTime/60, totalTime%60)).replace(" ", "0")

if __name__ == "__main__":
    main()
