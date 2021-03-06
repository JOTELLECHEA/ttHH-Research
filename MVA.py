#!/cvmfs/sft.cern.ch/lcg/releases/LCG_94/Python/2.7.15/x86_64-slc6-gcc62-opt/bin/python
import sklearn 

if sklearn.__version__ == '0.20.4':
    from sklearn.model_selection import train_test_split
else :
    from sklearn.cross_validation import train_test_split
    
import csv,sys
import argparse
import numpy as np
import pandas as pd 
from ROOT import*
from numpy import array
from os import system
from datetime import datetime
import matplotlib.pyplot as plt
from root_numpy import root2array, rec2array
from sklearn import datasets
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import classification_report, roc_auc_score, roc_curve, auc
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

def prRed(prt): print("\033[91m {}\033[00m" .format(prt))
np.set_printoptions(threshold=np.inf)
file= 'ROC_data'
tree = 'OutputTree'

parser = argparse.ArgumentParser(description= 'BDT for ttHH and background')
parser.add_argument("--branch", default='wrong', type=str, help= "Use '--branch=' followed by a branch_name")

args = parser.parse_args()
branch = str(args.branch)

bn_phase1   = """njet""".split(",")
bn_phase2   = """njet,btag,srap""".split(",")
bn_phase3   = """njet,btag,srap,cent,m_bb,h_b""".split(",")
bn_phase4   = """njet,btag,srap,cent,m_bb,h_b,mt1,mt2,mt3,dr1,dr2,dr3""".split(",")
bn_phase5   = """njet,btag,srap,cent,m_bb,h_b,mt1,mt2,mt3,dr1,dr2,dr3,chi""".split(",")

while True:
    try:
        if branch == 'phase1':
            print 'You selected option:', branch
            branch_names = bn_phase1
            name = file + '_' + branch + '.csv'
            break
        elif branch == 'phase2':
            print 'You selected option:', branch
            branch_names = bn_phase2
            name = file + '_' + branch + '.csv'
            break
        elif branch == 'phase3':
            print 'You selected option:', branch
            branch_names = bn_phase3
            name = file + '_' + branch + '.csv'
            break
        elif branch == 'phase4':
            print 'You selected option:', branch
            branch_names = bn_phase4
            name = file + '_' + branch  + '.csv'
            break
        elif branch == 'phase5':
            print 'You selected option:', branch
            branch_names = bn_phase5
            name = file + '_' + branch + '.csv'
            break
        elif branch == 'wrong':
            sys.exit('Need to pass a variable, use --h for options')
    except NameError:
        system('clear')
        prRed('*******************Invalid option **************\n')
        break


branch_names = [c.strip() for c in branch_names]
branch_names = (b.replace(" ", "_") for b in branch_names)
branch_names = list(b.replace("-", "_") for b in branch_names)

signal = root2array('new_signal_tthh.root',tree, branch_names, include_weight=True)
signal = rec2array(signal)

bg_ttbb   = root2array('new_background_ttbb.root', tree, branch_names, include_weight=True)
bg_ttZ    = root2array('new_background_ttZ.root' , tree, branch_names, include_weight=True)
bg_ttH    = root2array('new_background_ttH.root' , tree, branch_names, include_weight=True)
background    = np.concatenate((bg_ttbb,bg_ttH,bg_ttZ))
background    = rec2array(background)

X = np.concatenate((signal, background)) 
y = np.concatenate((np.ones(signal.shape[0]), np.zeros(background.shape[0])))
X_dev,X_eval, y_dev,y_eval = train_test_split(X, y, test_size = 0.10, random_state=42)
X_train,X_test, y_train,y_test, = train_test_split(X_dev, y_dev, test_size = 0.5,random_state=42)             


dt = DecisionTreeClassifier(max_depth=5, min_samples_split=2, splitter='best')
bdt = AdaBoostClassifier(dt, algorithm ='SAMME', n_estimators=1000, learning_rate=1.0)
model = bdt.fit(X_train, y_train)
y_predicted = bdt.predict(X_test)
print classification_report(y_test, y_predicted,target_names=["background", "signal"])
print "Area under ROC curve: %.4f"%(roc_auc_score(y_test,bdt.decision_function(X_test)))
#########################################################################################
def plotFeatureImportances(features, importances):
    imps=importances[:-1]
    y_pos=np.arange(len(features))
    plt.clf()
    indices = np.argsort(imps)
    plt.barh(y_pos, np.sort(imps))
    labels=[features[k] for k in indices]
    plt.yticks(y_pos, labels)
    plt.xlabel('F score')
    plt.ylabel('Feature')
    plt.savefig('features_' + branch + '.png',dpi = 100)

plotFeatureImportances(branch_names, model.feature_importances_)

decisions = bdt.decision_function(X_test)
fpr, tpr, thresholds = roc_curve(y_test, decisions)
roc_auc = auc(fpr, tpr)
plt.subplot(211)
plt.plot(fpr, tpr, lw=1, label='ROC (area = %0.6f)'%(roc_auc))
plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Luck')
plt.xlim([-0.05, 1.05])
plt.ylim([-0.05, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")
plt.grid()

#BDT Distribution
def compare_train_test(clf, X_train, y_train, X_test, y_test, bins=30):
    decisions = []
    for X,y in ((X_train, y_train), (X_test, y_test)):
        d1 = clf.decision_function(X[y>0.5]).ravel()
        d2 = clf.decision_function(X[y<0.5]).ravel()
        decisions += [d1, d2]
    low = min(np.min(d) for d in decisions)
    high = max(np.max(d) for d in decisions)
    low_high = array([low,high])
    
    r00  = ['name','var']
    r6  = ['lh',low_high]
    plt.subplot(212)
    plt.hist(decisions[0],color='r', alpha=0.5, range=low_high, bins=bins,histtype='stepfilled', density=True,label='S (train)')
    plt.hist(decisions[1],color='b', alpha=0.5, range=low_high, bins=bins,histtype='stepfilled', density=True,label='B (train)')

    hist, bins = np.histogram(decisions[2],bins=bins, range=low_high, density=True)
    scale = len(decisions[2]) / sum(hist)
    err = np.sqrt(hist * scale) / scale
    r0  = ['d0',decisions[0]]
    r1  = ['d1',decisions[1]]


    width = (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    plt.errorbar(center, hist, yerr=err, fmt='o', c='r', label='S (test)')

    hist, bins = np.histogram(decisions[3],bins=bins, range=low_high, density=True)
    scale = len(decisions[2]) / sum(hist)
    err = np.sqrt(hist * scale) / scale
    r2  = ['d2',decisions[2]]
    r3  = ['d3',decisions[3]]
    plt.errorbar(center, hist, yerr=err, fmt='o', c='b', label='B (test)')
    
    r4  = ['fpr',fpr]
    r5  = ['tpr',tpr]
    r7  = ['thresholds',thresholds]

    with open(name, 'a') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(r00)
        writer.writerow(r0)
        writer.writerow(r1)
        writer.writerow(r2)
        writer.writerow(r3)
        writer.writerow(r4)
        writer.writerow(r5)
        writer.writerow(r6)
        writer.writerow(r7)

    csvFile.close()
################################################################################################


    plt.xlabel('BDT output')
    plt.ylabel('Arbitrary units')
    plt.legend(loc='upper left')
    plt.yscale('log')
    plt.show()
    
compare_train_test(bdt, X_train, y_train, X_test, y_test)

BDToutput_test = 'BDToutput_test' + '_' + branch  + '.root'

# BDT to TTree
from root_numpy import array2root
y_predicted = bdt.decision_function(X)
y_predicted.dtype = [('y', np.float64)]
array2root(y_predicted, BDToutput_test, branch)

plt.show()
