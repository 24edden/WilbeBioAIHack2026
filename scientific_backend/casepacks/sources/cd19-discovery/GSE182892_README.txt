### ====================================
All scripts can be found in: https://github.com/mcortes-lopez/CD19_splicing_mutagenesis/tree/main/demultiplexing_scripts/RNAseq
###=======================================

##-------------------------------
## read length + composition
##-------------------------------

Read1: 350bp
Read2: 250bp

Read1: random:10N---20bpFixedSeqForPrimerBinding---anchor1:TGCAGAATTC---barcode:15N---anchor2:GGATCC---READ1
Read2: random:10N---20bpFixedSeqForPrimerBinding---READ2

(occasionally, the barcode can be longer or shorter than 15N)



##---------------------------------------------------
## quality trim multiplexed reads
##
## used tool: trimmomatic (v0.36)
##---------------------------------------------------

java -jar trimmomatic-0.36.jar PE -threads 16 -phred33 -trimlog trimmomatic.log RAWDATA.R1.fastq.gz RAWDATA.R2.fastq.gz FILTEREDDATA.R1.fastq.gz FILTEREDDATA.R1.unpaired.fastq.gz FILTEREDDATA.R2.fastq.gz FILTEREDDATA.R2.unpaired.fastq.gz SLIDINGWINDOW:6:10 MINLEN:0 



##----------------------------------------------------------
## barcode pattern matching and trimming:
## 
##    - keep all read pairs long enough to overlap exon junctions, i.e. 
##      remove all read pairs, whose length before barcode trimming is
##            length(read1) < 305 || length(read2) < 157),
##
##    - find anchor sequences (pattern match), extract barcodes, 
## 
##    - remove front of read1 incl. barcode, anchors and primer2 and add 
##      barcode to read names
##
## used tool: R (v3.5.1)
##----------------------------------------------------------

mkdir -p DEMULTIDIR

R CMD BATCH --vanilla --inputPath=RAWDATADIR --outputPath=DEMULTIDIR --Read1=FILTEREDDATA.R1.fastq.gz --Read2=FILTEREDDATA.R2.fastq.gz --barcodelength=15 --minlengthread1=305 --minlengthread2=157 patternmatching.rna.barcodes.R patternmatch.rna.barcodes.log

## output data files needed for further processing: FILTEREDDATA.R1.trimmedBC.fastq.gz 
## (in folder DEMULTIDIR)                           FILTEREDDATA.R2.trimmedBC.fastq.gz



##----------------------------------------------------------
## trim off possible end of primer1 at the end of read1 
## 
## min. length to keep: 244 = 305 (min.length of full read) - 61 (=10Nrandom+20bpPrimer2+10bpAnchor+15Nbarcode+6bpAnchor)
##
## tool: cutadapt (v1.6)
##----------------------------------------------------------

cutadapt --adapter=TAGAGGTTCC --overlap=3 --error-rate=0.1 --no-indels --minimum-length=244 --pair-filter=both --output=DEMULTIDIR/FILTEREDDATA.R1.trimmedBC.trimmedPrimer.fastq.gz --paired-output=DEMULTIDIR/FILTEREDDATA.R2.trimmedBC.trimmedPrimer.fastq.gz --too-short-output=DEMULTIDIR/FILTEREDDATA.R1.trimmedBC.trimmedPrimer.tooshort.fastq.gz --too-short-paired-output=DEMULTIDIR/FILTEREDDATA.R2.trimmedBC.trimmedPrimer.tooshort.fastq.gz DEMULTIDIR/FILTEREDDATA.R1.trimmedBC.fastq.gz DEMULTIDIR/FILTEREDDATA.R2.trimmedBC.fastq.gz &> cutadapt.log



##----------------------------------------------------------
##
## demultiplex
##
## tool: R (v3.5.1)
##
##----------------------------------------------------------

mkdir -p DEMULTIDIR/read1/
mkdir -p DEMULTIDIR/read2/

R CMD BATCH --vanilla --inputPath=DEMULTIDIR --outputPath=DEMULTIDIR/read1/ --fastqfile=FILTEREDDATA.R1.trimmedBC.trimmedPrimer.fastq.gz --lib=DATASET_NAME --read=1 separate.barcodes.R separate.barcodes.read1.log

R CMD BATCH --vanilla --inputPath=DEMULTIDIR --outputPath=DEMULTIDIR/read2/ --fastqfile=FILTEREDDATA.R2.trimmedBC.trimmedPrimer.fastq.gz --lib=DATASET_NAME --read=2 separate.barcodes.R separate.barcodes.read2.log



##----------------------------------- CD19 genome sequence ---------------------------------------------------
>chr1
GACCACCGCCTTCCTCTCTGGGGGGACTGCCTGCCGCCCCCGCAGACACCCATGGTTGAGTGCCCTCCAGGCCCCTGCCTGCCCCAGCATCCCCTGCGCGAAGCTGGGTGCCCCGGAGAGTCTGACCACCATGCCACCTCCTCGCCTCCTCTTCTTCCTCCTCTTCCTCACCCCCATGGAAGTCAGGCCCGAGGAACCTCTAGTGGTGAAGGTGGAAGGTATGTCCAAAGGGCAGAAAGGGAAGGGATTGAGGCTGGAAACTTGAGTTGTGGCTGGGTGTCCTTGGCTGAGTAACTTACCCTCTCTGAGCCTCCATTTTCTTATTTGTAAAATTCAGGAAAGGGTTGGAAGGACTCTGCCGGCTCCTCCACTCCCAGCTTTTGGAGTCCTCTGCTCTATAACCTGGTGTGAGGAGTCGGGGGGCTTGGAGGTCCCCCCCACCCATGCCCACACCTCTCTCCCTCTCTCTCCACAGAGGGAGATAACGCTGTGCTGCAGTGCCTCAAGGGGACCTCAGATGGCCCCACTCAGCAGCTGACCTGGTCTCGGGAGTCCCCGCTTAAACCCTTCTTAAAACTCAGCCTGGGGCTGCCAGGCCTGGGAATCCACATGAGGCCCCTGGCCATCTGGCTTTTCATCTTCAACGTCTCTCAACAGATGGGGGGCTTCTACCTGTGCCAGCCGGGGCCCCCCTCTGAGAAGGCCTGGCAGCCTGGCTGGACAGTCAATGTGGAGGGCAGCGGTGAGGGCCGGGCTGGGGCAGGGGCAGGAGGAGAGAAGGGAGGCCACCATGGACAGAAGAGGTCCGCGGCCACAATGGAGCTGGAGAGAGGGGCTGGAGGGATTGAGGGCGAAACTCGGAGCTAGGTGGGCAGACTCCTGGGGCTTCGTGGCTTCAGTATGAGCTGCTTCCTGTCCCTCTACCTCTCACTGTCTTCTCTCTCTCTGCGGGTCTTTGTCTCTATTTATCTCTGTCTTTGAGTCTCTATCTCTCTCCCTCTCCTGGGTGTCTCTGCATTTGGTTCTGGGTCTCTTCCCAGGGGAGCTGTTCCGGTGGAATGTTTCGGACCTAGGTGGCCTGGGCTGTGGCCTGAAGAACAGGTCCTCAGAGGGCCCCAGCTCCCCTTCCGGGAAGCTCATGAGCCCCAAGCTGTATGTGTGGGCCAAAGACCGCCCTGAGATCTGGGAGGGAGAGCCTCCGTGTCTCCCACCGAGGGACAGCCTGAACCAGAGCCTCAGCCAGGGTATGGTGATGACTGGGGAGATGCCGGGAA
