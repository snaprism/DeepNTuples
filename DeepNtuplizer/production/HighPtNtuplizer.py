import FWCore.ParameterSet.Config as cms

import FWCore.ParameterSet.VarParsing as VarParsing

### parsing job options
import sys

options = VarParsing.VarParsing()

options.register(
    "inputScript",
    "",
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.string,
    "input Script",
)
options.register(
    "outputFile",
    "output",
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.string,
    "output File (w/o .root)",
)
options.register(
    "maxEvents",
    101,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.int,
    "maximum events",
)
options.register(
    "skipEvents",
    0,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.int,
    "skip N events",
)
options.register(
    "job",
    0,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.int,
    "job number",
)
options.register(
    "nJobs",
    1,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.int,
    "total jobs",
)
options.register(
    "reportEvery",
    100,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.int,
    "report every",
)
options.register(
    "gluonReduction",
    0.0,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.float,
    "gluon reduction",
)
options.register(
    "selectJets",
    True,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.bool,
    "select jets with good gen match",
)
options.register(
    "phase2",
    False,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.bool,
    "apply jet selection for phase 2. Currently sets JetEtaMax to 3.0 and picks slimmedJetsPuppi as jet collection.",
)
options.register(
    "puppi",
    False,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.bool,
    "use puppi jets",
)
options.register(
    "eta",
    False,
    VarParsing.VarParsing.multiplicity.singleton,
    VarParsing.VarParsing.varType.bool,
    "use eta up to 5.0",
)


import os

release = os.environ["CMSSW_VERSION"][6:]
print("Using release " + release)


options.register(
    "inputFiles",
    "",
    VarParsing.VarParsing.multiplicity.list,
    VarParsing.VarParsing.varType.string,
    "input files (default is the tt RelVal)",
)

if hasattr(sys, "argv"):
    options.parseArguments()


if options.puppi:
    usePuppi = True
else:
    usePuppi = False

process = cms.Process("HighPtTagger")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.EventContent.EventContent_cff")
process.load("Configuration.StandardSequences.Services_cff")
process.load("Configuration.StandardSequences.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.MagneticField_38T_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

from Configuration.AlCa.GlobalTag import GlobalTag

#'auto:run2_mc'
process.GlobalTag = GlobalTag(process.GlobalTag, "106X_mc2017_realistic_v8", "")

process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))

process.MessageLogger.cerr.FwkReport.reportEvery = options.reportEvery

process.options = cms.untracked.PSet(
    allowUnscheduled=cms.untracked.bool(True), wantSummary=cms.untracked.bool(False)
)

process.load("DeepNTuples.DeepNtuplizer.samples.HighPt_cfg")

if options.inputFiles:
    process.source.fileNames = options.inputFiles

if (
    options.inputScript != ""
    and options.inputScript != "DeepNTuples.DeepNtuplizer.samples.TTJetsPhase1_cfg"
):
    process.load(options.inputScript)

numberOfFiles = len(process.source.fileNames)
numberOfJobs = options.nJobs
jobNumber = options.job

process.source.fileNames = process.source.fileNames[
    jobNumber:numberOfFiles:numberOfJobs
]
if options.nJobs > 1:
    print("running over these files:")
    print(process.source.fileNames)

process.source.skipEvents = cms.untracked.uint32(options.skipEvents)
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(options.maxEvents))
releases = release.split("_")

# DeepNtuplizer
process.load("DeepNTuples.DeepNtuplizer.DeepNtuplizer_cfi")
process.deepntuplizer.jets = cms.InputTag("selectedUpdatedPatJetsDeepFlavour")
# process.deepntuplizer.bDiscriminators = bTagDiscriminators
# process.deepntuplizer.bDiscriminators.append('pfCombinedMVAV2BJetTags')
process.deepntuplizer.LooseSVs = cms.InputTag(
    "looseIVFinclusiveCandidateSecondaryVertices"
)

process.deepntuplizer.applySelection = cms.bool(options.selectJets)
if (int(releases[0]) > 8) or ((int(releases[0]) == 8) and (int(releases[1]) >= 4)):
    process.deepntuplizer.tagInfoName = cms.string("pfDeepCSV")

if options.eta:
    process.deepntuplizer.jetAbsEtaMax = cms.double(5.0)
    process.deepntuplizer.jetPtMin = cms.double(10.0)
else:
    process.deepntuplizer.jetAbsEtaMax = cms.double(2.5)
    process.deepntuplizer.jetPtMin = cms.double(15.0)

if options.phase2:
    process.deepntuplizer.jetAbsEtaMax = cms.double(3.0)

process.deepntuplizer.gluonReduction = cms.double(options.gluonReduction)


outFileName = options.outputFile + "_" + str(options.job) + ".root"
print("Using output file " + outFileName)

process.TFileService = cms.Service("TFileService", fileName=cms.string(outFileName))

process.p = cms.Path(process.deepntuplizer)
