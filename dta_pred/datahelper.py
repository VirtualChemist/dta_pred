## SOME OF THE METHODS AND CLASSES ARE TAKEN FROM github.com/hkmztrk/deepdta

import json
import pickle
from collections import OrderedDict
import pandas as pd
import numpy as np
from os import path
import sys
from sklearn.model_selection import KFold, PredefinedSplit
#from keras.preprocessing.sequence import pad_sequences


## ######################## ##
#
#  Define CHARSET, CHARLEN
#
## ######################## ## 

# CHARPROTSET = { 'A': 0, 'C': 1, 'D': 2, 'E': 3, 'F': 4, 'G': 5, 'H': 6, \
#             'I': 7, 'K': 8, 'L': 9, 'M': 10, 'N': 11, 'P': 12, 'Q': 13, \
#             'R': 14, 'S': 15, 'T': 16, 'V': 17, 'W': 18, 'Y': 19, 'X': 20, \
#             'O': 20, 'U': 20,
#             'B': (2, 11),
#             'Z': (3, 13),
#             'J': (7, 9) }
# CHARPROTLEN = 21

CHARPROTSET = { "A": 1, "C": 2, "B": 3, "E": 4, "D": 5, "G": 6,
                "F": 7, "I": 8, "H": 9, "K": 10, "M": 11, "L": 12,
                "O": 13, "N": 14, "Q": 15, "P": 16, "S": 17, "R": 18,
                "U": 19, "T": 20, "W": 21,
                "V": 22, "Y": 23, "X": 24,
                "Z": 25 }

CHARPROTLEN = 25

CHARCANSMISET = { "#": 1, "%": 2, ")": 3, "(": 4, "+": 5, "-": 6,
                  ".": 7, "1": 8, "0": 9, "3": 10, "2": 11, "5": 12,
                  "4": 13, "7": 14, "6": 15, "9": 16, "8": 17, "=": 18,
                  "A": 19, "C": 20, "B": 21, "E": 22, "D": 23, "G": 24,
                  "F": 25, "I": 26, "H": 27, "K": 28, "M": 29, "L": 30,
                  "O": 31, "N": 32, "P": 33, "S": 34, "R": 35, "U": 36,
                  "T": 37, "W": 38, "V": 39, "Y": 40, "[": 41, "Z": 42,
                  "]": 43, "_": 44, "a": 45, "c": 46, "b": 47, "e": 48,
                  "d": 49, "g": 50, "f": 51, "i": 52, "h": 53, "m": 54,
                  "l": 55, "o": 56, "n": 57, "s": 58, "r": 59, "u": 60,
                  "t": 61, "y": 62}

CHARCANSMILEN = 62

CHARISOSMISET = {"#": 29, "%": 30, ")": 31, "(": 1, "+": 32, "-": 33, "/": 34, ".": 2,
                 "1": 35, "0": 3, "3": 36, "2": 4, "5": 37, "4": 5, "7": 38, "6": 6,
                 "9": 39, "8": 7, "=": 40, "A": 41, "@": 8, "C": 42, "B": 9, "E": 43,
                 "D": 10, "G": 44, "F": 11, "I": 45, "H": 12, "K": 46, "M": 47, "L": 13,
                 "O": 48, "N": 14, "P": 15, "S": 49, "R": 16, "U": 50, "T": 17, "W": 51,
                 "V": 18, "Y": 52, "[": 53, "Z": 19, "]": 54, "\\": 20, "a": 55, "c": 56,
                 "b": 21, "e": 57, "d": 22, "g": 58, "f": 23, "i": 59, "h": 24, "m": 60,
                 "l": 25, "o": 61, "n": 26, "s": 62, "r": 27, "u": 63, "t": 28, "y": 64}

CHARISOSMILEN = 64


## ######################## ##
#
#  Encoding Helpers
#
## ######################## ## 

#  Y = -(np.log10(Y/(math.pow(math.e,9))))

def one_hot_smiles(line, MAX_SMI_LEN, smi_ch_ind):
    X = np.zeros((MAX_SMI_LEN, len(smi_ch_ind))) #+1

    for i, ch in enumerate(line[:MAX_SMI_LEN]):
        X[i, (smi_ch_ind[ch]-1)] = 1

    return X

def one_hot_sequence(line, MAX_SEQ_LEN, smi_ch_ind):
    X = np.zeros((MAX_SEQ_LEN, len(smi_ch_ind)))
    for i, ch in enumerate(line[:MAX_SEQ_LEN]):
        X[i, (smi_ch_ind[ch])-1] = 1

    return X

def label_smiles(line, MAX_SMI_LEN, smi_ch_ind):
    X = np.zeros(MAX_SMI_LEN)
    for i, ch in enumerate(line[:MAX_SMI_LEN]): #	x, smi_ch_ind, y
        X[i] = smi_ch_ind[ch]

    return X

def label_sequence(line, MAX_SEQ_LEN, smi_ch_ind):
    X = np.zeros(MAX_SEQ_LEN)

    for i, ch in enumerate(line[:MAX_SEQ_LEN]):
        X[i] = smi_ch_ind[ch]

    return X #.tolist()

## ######################## ##
#
#  DATASET Class
#
## ######################## ## 
# works for large dataset
class DataSet(object):
    def __init__(self, dataset_path, dataset_name, seqlen, smilen, protein_format='sequence', drug_format='labeled_smiles',
                 mol2vec_model_path=None, mol2vec_radius=1):
        self.SEQLEN = seqlen
        self.SMILEN = smilen
        #self.NCLASSES = n_classes
        self.charseqset = CHARPROTSET
        self.charseqset_size = CHARPROTLEN
        self.dataset_path = dataset_path
        self.fpath = path.join(dataset_path, dataset_name)

        self.charsmiset = CHARISOSMISET ###HERE CAN BE EDITED
        self.charsmiset_size = CHARISOSMILEN
        self.protein_format = protein_format
        self.drug_format = drug_format

        self.mol2vec_model_path = mol2vec_model_path
        self.mol2vec_radius = mol2vec_radius

    def parse_data(self):
        fpath = self.fpath

        print("Read %s start" % fpath)

        ligands = json.load(open(path.join(fpath, "ligands_can.txt")), object_pairs_hook=OrderedDict)

        if self.protein_format == 'sequence':
            proteins = json.load(open(path.join(fpath, "proteins.txt")), object_pairs_hook=OrderedDict)
        else:
            proteins = json.load(open(path.join(fpath, "proteins_hhmake.txt")), object_pairs_hook=OrderedDict)

        if sys.version_info > (3, 0):
            Y = pickle.load(open(path.join(fpath, "Y"),"rb"), encoding='latin1')
        else:
            Y = pickle.load(open(path.join(fpath, "Y"),"rb"))

        XT = self.process_proteins(proteins)

        XD = self.process_ligands(ligands)

        Y = np.mat(np.copy(Y))
        XD, XT, Y = np.asarray(XD), np.asarray(XT), np.asarray(Y)
        label_row_inds, label_col_inds = np.where(np.isnan(Y) == False)

        return prepare_interaction_pairs(XD, XT, Y, label_row_inds, label_col_inds)

    def process_ligands(self, ligands):
        XD = []

        if self.drug_format == 'labeled_smiles':
            if type(ligands) == OrderedDict:
                iterator = ligands.keys()
            else:
                iterator = range(ligands.shape[0])

            for d in iterator:
                XD.append(label_smiles(ligands[d], self.SMILEN, self.charsmiset))
        elif self.drug_format == 'mol2vec':
            from rdkit.Chem import PandasTools
            from mol2vec.features import mol2alt_sentence, MolSentence, sentences2vec
            from gensim.models import word2vec

            word2vec_model = word2vec.Word2Vec.load(self.mol2vec_model_path)
            df_ligands = pd.DataFrame({'smiles': ligands})

            PandasTools.AddMoleculeColumnToFrame(df_ligands, 'smiles', 'ROMol')
            dtc_train = df_ligands[df_ligands['ROMol'].notnull()]
            dtc_train.loc[:, 'mol-sentence'] = dtc_train.apply(
                lambda x: MolSentence(mol2alt_sentence(x['ROMol'], self.mol2vec_radius)), axis=1)
            XD = sentences2vec(dtc_train['mol-sentence'], word2vec_model, unseen='UNK')

        return XD

    def process_proteins(self, proteins):
        XT = []
        if type(proteins) == OrderedDict:
            iterator = proteins.keys()
        else:
            iterator = range(proteins.shape[0])

        if self.protein_format == 'sequence':

            for t in iterator:
                XT.append(label_sequence(proteins[t], self.SEQLEN, self.charseqset))
        elif self.protein_format == 'pssm':
            for t in iterator:
                XT.append(get_PSSM(self.dataset_path, proteins[t], self.SEQLEN))
        else:
            raise NotImplementedError()

        return XT

class DTCDataset(DataSet):
    def parse_data(self, with_label=True):
        dtc_train = pd.read_csv(path.join(self.fpath, 'train_hhmake.csv'))
        dtc_train.drop('Unnamed: 0', axis=1, inplace=True)

        if with_label:
            dtc_train = dtc_train.groupby(['inchi_key', 'uniprot_id']).aggregate({'value': np.median, 'smiles': 'first',
                                                                                  'fasta': 'first',
                                                                                  'hhmake': 'first'}).reset_index()

        for ind in dtc_train[dtc_train['smiles'].str.contains('\n')].index:
            dtc_train.loc[ind, 'smiles'] = dtc_train.loc[ind, 'smiles'].split('\n')[0]

        n_samples = dtc_train['smiles'].shape[0]

        XD, XT = [1 for i in range(n_samples)], [1 for i in range(n_samples)]

        XD_processed = self.process_ligands(dtc_train['smiles'].unique())

        for i, smiles in enumerate(dtc_train['smiles'].unique()):
            indices = np.where(dtc_train['smiles'] == smiles)[0]

            for ind in indices:
                XD[ind] = XD_processed[i]

        XT_processed = self.process_proteins(dtc_train['hhmake' if self.protein_format =='pssm' else 'fasta'].unique())

        for i, fasta_seq in enumerate(dtc_train['fasta'].unique()):
            indices = np.where(dtc_train['fasta'] == fasta_seq)[0]

            for ind in indices:
                XT[ind] = XT_processed[i]

        assert len(XD) == len(XT) and len(XT) == dtc_train['smiles'].shape[0]

        if with_label:
            return XD, XT, dtc_train['value'].values
        else:
            return XD, XT

def get_PSSM(dataset_path, data_file, max_seq_len):
    pssm = np.loadtxt(path.join(dataset_path, 'davis_dtc', 'hhmake_pssm', data_file.split('/')[-1]))[:max_seq_len, :]

    half_left = int((max_seq_len-pssm.shape[0])/2)
    half_right = max_seq_len-pssm.shape[0] - half_left

    pssm = np.pad(pssm, [(half_left, half_right), (0, 0) ], 'constant')

    return pssm

def get_train_test_split_by_drugs(all_drugs, n_drugs_in_test=70, seed=42):
    if len(all_drugs.shape) == 1:
        all_drugs = np.reshape(all_drugs, (-1, 1))

    unique_drugs = np.unique(all_drugs, axis=0)

    assert n_drugs_in_test <= unique_drugs.shape[0]

    np.random.seed(seed)
    test_drugs = np.random.choice(unique_drugs.shape[0], n_drugs_in_test, )

    test_fold = np.ones(all_drugs.shape[0]) * -1

    test_samples = []
    for drug_ind in test_drugs:
        willbe_added = list(np.where((~(all_drugs == unique_drugs[drug_ind, :])).sum(axis=1) == 0)[0])
        test_samples += willbe_added

    assert len(test_samples) >= 1

    test_fold[test_samples] = 1

    return np.where(test_fold==-1)[0], np.where(test_fold==1)[0]

def prepare_interaction_pairs(XD, XT,  Y, rows, cols):
    drugs = []
    targets = []
    targetscls = []
    affinity=[]

    for pair_ind in range(len(rows)):
        drug = XD[rows[pair_ind]]
        drugs.append(drug)

        target=XT[cols[pair_ind]]
        targets.append(target)

        affinity.append(Y[rows[pair_ind],cols[pair_ind]])

    drug_data = np.asarray(np.stack(drugs))
    target_data = np.asarray(np.stack(targets))

    assert drug_data.shape[0] == target_data.shape[0] and target_data.shape[0] == len(affinity)

    return drug_data,target_data,  affinity

def get_n_fold_by_drugs(all_drugs, n_splits=5):
    unique_drugs = np.unique(all_drugs, axis=0)
    test_folds = np.ones(all_drugs.shape[0])
    kf = KFold(n_splits, random_state=15)

    j = 0
    for _, validation_drugs in kf.split(np.arange(unique_drugs.shape[0])):
        val_inds = []

        for drug_ind in validation_drugs:
            willbe_added = list(np.where((~(all_drugs == unique_drugs[drug_ind, :])).sum(axis=1) == 0)[0])
            val_inds += willbe_added
        test_folds[val_inds] = j
        j += 1

    return PredefinedSplit(test_folds)

def load_data(FLAGS):
    dataset = DataSet( dataset_path = FLAGS.dataset_path,
                       dataset_name='davis',
                       seqlen = FLAGS.max_seq_len,
                       smilen = FLAGS.max_smi_len,
                       protein_format=FLAGS.protein_format,
                       drug_format=FLAGS.drug_format,
                       mol2vec_model_path=FLAGS.mol2vec_model_path,
                       mol2vec_radius=FLAGS.mol2vec_radius
                       )

    XD_davis, XT_davis, Y_davis = dataset.parse_data()

    dtc_dataset = DTCDataset(dataset_path=FLAGS.dataset_path,
                        dataset_name='dtc',
                        seqlen=FLAGS.max_seq_len,
                        smilen=FLAGS.max_smi_len,
                        protein_format=FLAGS.protein_format,
                        drug_format=FLAGS.drug_format,
                        mol2vec_model_path=FLAGS.mol2vec_model_path,
                        mol2vec_radius=FLAGS.mol2vec_radius
                           )

    XD_dtc, XT_dtc, Y_dtc = dtc_dataset.parse_data()

    all_train_drugs = np.concatenate((np.asarray(XD_davis), np.asarray(XD_dtc)), axis=0)

    all_train_prots = np.concatenate((np.asarray(XT_davis), np.asarray(XT_dtc)), axis=0)
    all_train_Y = np.concatenate((np.asarray(Y_davis), np.asarray(Y_dtc)), axis=0)
    all_train_Y = -np.log10(all_train_Y/1e9)

    shuffled_inds = np.asarray([i for i in range(all_train_Y.shape[0])])

    for i in range(0, 3):
        np.random.seed(FLAGS.seed)
        np.random.shuffle(shuffled_inds)

    return all_train_drugs[shuffled_inds], all_train_prots[shuffled_inds], all_train_Y[shuffled_inds]