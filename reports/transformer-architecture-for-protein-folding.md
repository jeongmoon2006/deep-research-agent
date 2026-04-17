# Deep Research Report: Transformer Architecture for Protein Folding

**Date**: 2026-04-17
**Papers surveyed**: 100
**Search strategy**: Multi-query search across arXiv and Semantic Scholar, ranked by citation count (45%), influential citations (30%), recency (25%)

---

> **Critical Preliminary Note on Corpus Quality**
>
> A systematic review of the 100 retrieved papers reveals a severe mismatch between the stated search topic ("transformer architecture for protein folding") and the actual corpus content. The overwhelming majority of retrieved papers address unrelated domains: epileptic seizure detection (Tang et al., 2024; Li et al., 2023), human activity recognition (Mekruksavanich et al., 2023; Xu et al., 2025), drug combination prediction (Wang et al., 2021), miRNA-disease associations (Biyu et al., 2024; Dai et al., 2025), air pollution prediction (Fong et al., 2025), image enhancement (Mastan & Raman, 2020), fluid dynamics (Lye et al., 2019), and bug-tracker labeling (Lyubinets et al., 2018), among others. Fewer than fifteen papers are substantively relevant to transformer architectures applied to protein folding or closely related protein structure tasks. The report below is structured to provide maximum scientific value from the available evidence, explicitly distinguishing what the corpus directly supports from what must be inferred or noted as absent. All factual claims are grounded in the provided papers; no speculation beyond the corpus is introduced.

---

## 1. What Are Researchers Studying in This Field?

### 1.1 The Protein Structure Prediction Problem

The protein folding problem — determining the three-dimensional native conformation of a protein from its primary amino acid sequence — has been a central challenge in computational biology for decades (van Gils et al., 2023; Lei & Huang, 2010; Thirumalai & Klimov, 2001). The biological motivation is straightforward: protein function is determined by three-dimensional structure, and understanding that structure is foundational to drug discovery, enzyme engineering, and disease analysis (Zhang et al., 2025; Rossi et al., 2025). Within the surveyed corpus, several distinct but related research threads can be identified.

### 1.2 Deep Learning Architectures for Protein Structure Prediction

The most directly relevant strand of research concerns the application of deep learning, and specifically transformer-based and attention-based architectures, to protein structure prediction and related tasks. Zhang et al. (2025) provide a broad survey of advanced deep learning methods for protein structure prediction and design, explicitly examining diffusion-based frameworks and novel pairwise attention modules following AlphaFold's impact on the field. They identify the Evoformer — the transformer-based core module of AlphaFold — as a landmark architecture, noting that its depth (48 stacked blocks) introduces substantial computational costs (Sanford et al., 2025). Abbaszadeh & Shahlaee (2025) study AlphaFold 3 specifically, characterizing its multi-scale transformer architectures and biologically informed cross-attention mechanisms as transformative advances in structural biology. The paper by Zhou et al. (2024) addresses protein secondary structure prediction via integrated transformer and convolutional neural network (CNN) architectures, representing a more targeted effort to apply attention mechanisms at the level of secondary structure rather than full three-dimensional prediction.

### 1.3 Protein Fold Recognition

Separate from ab initio folding, fold recognition (threading) asks which known fold class a query protein sequence belongs to. Han et al. (2022) study this task using a stack convolutional neural network enhanced with an attention mechanism, treating fold recognition as a pattern classification problem over protein sequences. Goel et al. (2025) extend this line of work by fusing evolutionary information (in the form of position-specific scoring matrices and multiple sequence alignments) with attention-based deep neural networks, framing fold prediction as a retrieval and classification problem over known structural families.

### 1.4 Protein Stability Prediction and Mutation Effects

A related but distinct research focus concerns predicting how point mutations alter protein stability (ΔΔG). Pak et al. (2023) address this using a large-scale dataset combined with deep neural networks, arguing that data scarcity has historically limited progress relative to structure prediction. Barducci et al. (2026) introduce JanusDDG, a physics-informed neural network for sequence-based protein stability prediction using a "two-fronts attention" mechanism. Xu et al. (2025) develop a self-attention-driven sparse convolutional network for protein thermostability prediction, integrating sequence, mutation relationship, and physicochemical property encodings. Rossi et al. (2025) take a complementary approach, applying mass-balance approximations of unfolding to improve potential-like (non-deep-learning) methods for stability prediction.

### 1.5 Protein Loop Modeling

Wang et al. (2023) present KarmaLoop, a deep learning paradigm for full-atom protein loop modeling, targeting atomic-accuracy reconstruction of loop regions — the most conformationally variable segments of protein structures. Das (2012) provides an earlier, non-deep-learning approach to loop prediction using an RNA-inspired structural ansatz. These works collectively acknowledge that loop modeling remains among the hardest sub-problems within structure prediction (Wang et al., 2023).

### 1.6 Protein Language Models and Downstream Prediction Tasks

Across the corpus, protein language models (PLMs) — large transformer models pre-trained on protein sequence databases — appear as feature extractors for diverse downstream tasks. Beck et al. (2024) study Metalic, a meta-learning framework for in-context adaptation of protein language models to biophysical and functional prediction tasks when labeled data is scarce. Akbar et al. (2025) employ PLMs as feature sources for neuropeptide prediction. Gao et al. (2025) use multi-source PLMs for phage host prediction. These papers collectively represent a transfer-learning paradigm where transformer-generated representations underpin predictive models.

### 1.7 HP Model and Reinforcement Learning

Two papers study the simplified Hydrophobic-Polar (HP) lattice model as an abstraction of protein folding. Yang et al. (2022) apply deep reinforcement learning to HP model folding on 2D and 3D lattices. Liu & Iba (2025) extend this by integrating transformer-based attention layers (Deep Q-Network with attention) into the 3D HP folding problem, explicitly testing whether transformer architectures improve search in combinatorial conformational spaces.

### 1.8 AlphaFold-Specific Analyses

Several papers focus on evaluating or extending AlphaFold outputs rather than proposing new architectures. Brems et al. (2022) analyze AlphaFold predictions for topologically complex proteins (knotted proteins), discovering a 7₁-knot among high-confidence predictions. Chakravarty et al. (2024) review blind spots in AlphaFold-based prediction, specifically proteins with alternative conformational states or switchable folds that AlphaFold systematically mishandles. Jahagirdar (2024) applies knot theory to assess and potentially improve the AlphaFold Protein Database. Abbaszadeh & Shahlaee (2025) reframe AlphaFold 3 as a differentiable framework for structural biology more broadly.

---

## 2. What Data Do They Collect?

### 2.1 Protein Sequence Databases

The primary data source across protein-focused papers is amino acid sequence data. Goel et al. (2025) use multiple sequence alignments (MSAs) and evolutionary profiles (position-specific scoring matrices, PSSMs) derived from sequence databases such as UniRef and BFD, following the AlphaFold paradigm (Abbaszadeh & Shahlaee, 2025). Zhou et al. (2024) train on labeled protein sequences from the Protein Data Bank (PDB), where ground-truth secondary structure annotations are available from DSSP (Dictionary of Secondary Structure of Proteins) assignments. Han et al. (2022) use benchmark fold recognition datasets, including the SCOP (Structural Classification of Proteins) hierarchy.

### 2.2 Protein Structure Databases

Three-dimensional structural data originates primarily from the PDB, which contains experimentally determined structures from X-ray crystallography, NMR, and cryo-electron microscopy. Zhang et al. (2025) and Abbaszadeh & Shahlaee (2025) rely on PDB-derived structural data for training and validation. Wang et al. (2023) use PDB loop structures as both training targets and benchmarks for loop modeling accuracy. Brems et al. (2022) analyze high-confidence AlphaFold predictions from the AlphaFold Protein Database (AFDB), rather than experimental structures. Liu et al. (2025) incorporate AlphaFold2-generated structural data for protein function prediction tasks, reflecting the growing use of computationally predicted structures as training data.

### 2.3 Mutation Stability Datasets

For stability prediction, Pak et al. (2023) compile a "mega dataset" aggregating multiple experimental ΔΔG measurements from sources including ProThermDB, S2648, and other curated mutation databases, totaling substantially more training examples than previously available. Barducci et al. (2026) and Xu et al. (2025) draw on similar compilations of experimental thermodynamic measurements. Rossi et al. (2025) use these datasets to benchmark both learning-based and potential-like methods.

### 2.4 HP Model Lattice Simulations

Yang et al. (2022) and Liu & Iba (2025) use synthetically generated HP sequences of varying lengths as their primary data source, with the "label" being the maximum number of H-H contacts achievable on a 2D or 3D lattice. Ground-truth optimal conformations are known for short sequences via exhaustive enumeration, providing exact supervision signals.

### 2.5 Protein Language Model Representations

Beck et al. (2024) use protein sequence embeddings generated by pre-trained large language models (ESM-family models) as input features for downstream task prediction, with in vitro biophysical annotations from DMS (deep mutational scanning) experiments or assay databases as labels.

### 2.6 Data from Tangentially Related Domains (Non-Protein)

The majority of papers in the corpus collect data entirely unrelated to protein folding: EEG recordings for seizure detection (Tang et al., 2024; Li et al., 2023), inertial measurement unit (IMU) data from smartphones for activity recognition (Mekruksavanich et al., 2023; Xu et al., 2025), plasma biomarker and neuroimaging data for depression diagnosis (Jiang et al., 2024), CT imaging for stroke prediction (Zhang et al., 2023), audio signals (Medhat et al., 2018), and software bug-tracker text (Lyubinets et al., 2018). These papers contribute no protein-relevant data and are noted here only for completeness of corpus accounting.

---

## 3. How Do They Model It?

### 3.1 Transformer and Self-Attention Architectures

The defining architectural innovation in the field is the transformer, introduced for NLP and subsequently adapted for biological sequences and structures. The Evoformer, the core of AlphaFold2, operates on two representations simultaneously: a multiple sequence alignment (MSA) representation capturing evolutionary information across homologs, and a pair representation encoding pairwise residue relationships. Abbaszadeh & Shahlaee (2025) describe how AlphaFold 3 extends this framework with multi-scale transformer architectures and cross-attention mechanisms that jointly process protein sequences, structural geometry, and interacting molecular partners. Zhang et al. (2025) characterize novel pairwise attention modules and diffusion-based frameworks as the next generation of such architectures.

Sanford et al. (2025) propose replacing the 48-block Evoformer with a Neural Ordinary Differential Equation (Neural ODE) framework that treats the depth dimension as a continuous variable rather than discrete stacked blocks. Their motivation is explicitly to reduce the computational cost of the Evoformer while preserving its representational capacity for spatial and evolutionary constraints (Sanford et al., 2025).

Zhou et al. (2024) construct a hybrid architecture combining a transformer encoder for long-range sequence dependencies with a CNN for local sequence features, applied to secondary structure prediction. This pattern — transformer for global context, CNN for local features — recurs across the corpus (Akbar et al., 2025; Gao et al., 2025).

### 3.2 Attention Mechanisms in Protein-Adjacent Tasks

Chen et al. (2020) study the role of attention mechanisms specifically in protein residue-residue contact prediction, finding that attention weights provide interpretable proxies for evolutionary covariation signals. They use a deep residual network augmented with attention heads, demonstrating that the attention-derived contact maps recapitulate coevolutionary patterns from MSAs. This work is correlational: attention weights correlate with known coevolutionary signals but do not establish causal explanations.

Han et al. (2022) model fold recognition as a metric learning problem, using a stack of convolutional layers followed by attention pooling to produce fold-discriminative feature vectors. The attention mechanism selects the most informative positions along the sequence for fold classification.

Goel et al. (2025) fuse evolutionary profiles (PSSMs) with raw sequence encodings via a multi-head self-attention layer, arguing that attention enables the model to weight informative alignment columns differentially.

### 3.3 Graph Neural Networks for Protein Structure

Graph neural networks (GNNs) appear as a common architectural choice for tasks defined over protein structures, where amino acids are nodes and spatial or sequence-proximity edges connect them. AGF-PPIS (Fu et al., 2024) applies graph convolutional networks (GCNs) with multi-head self-attention for protein-protein interaction (PPI) site prediction. Animesh et al. (2024) employ an equivariant graph neural network (E(Q)AGNN) enhanced with attention for PPI site prediction, using SE(3)-equivariant message passing to respect the rotational and translational symmetry of three-dimensional structures.

Zhang et al. (2024) present FuncPhos-STR, which uses AlphaFold-predicted structures as input to a GNN for functional phosphorylation site prediction, combining structural geometry with sequence and dynamics features. Song et al. (2024) apply channel-attention CNNs for protein-DNA binding residue prediction.

### 3.4 Protein Language Model Fine-tuning and In-Context Learning

Beck et al. (2024) treat protein language models as frozen feature extractors and learn adaptation mechanisms (in-context learning heads) that generalize across fitness prediction tasks with few labeled examples. This approach sidesteps full fine-tuning of billion-parameter models, which would require extensive computational resources.

Akbar et al. (2025) use protein language model embeddings in combination with FastText encodings as multi-view features fed to a capsule neural network for neuropeptide prediction, illustrating how transformer-derived representations can be combined with other encoding schemes.

### 3.5 Reinforcement Learning and HP Models

Yang et al. (2022) formulate 3D HP folding as a sequential decision problem, applying policy gradient and Q-learning algorithms. Liu & Iba (2025) augment the Deep Q-Network with transformer attention layers, enabling the agent to condition its folding decisions on representations of the entire partial conformation rather than only local features. They compare transformer-augmented DQN against CNN-based and LSTM-based baselines on standard HP benchmark sequences.

### 3.6 Physics-Informed and Hybrid Models

Barducci et al. (2026) introduce physics-informed constraints into a neural network for stability prediction, using a "two-fronts attention" mechanism that separately attends to the forward (unfolded) and reverse (native) directions of the sequence, inspired by thermodynamic cycle arguments. Rossi et al. (2025) hybridize machine learning with mass-balance approximations of unfolding thermodynamics, providing a computationally lightweight alternative to deep learning for stability prediction.

### 3.7 CNN and Recurrent Architectures for Secondary Structure

An older line of work predates transformers but remains in the corpus. Lin et al. (2016) propose MUST-CNN, a multilayer shift-and-stitch deep convolutional architecture for sequence-based prediction of solvent accessibility and secondary structure, drawing inspiration from image classification CNNs. Drori et al. (2019) use learned embeddings and deep architectures for protein structure prediction more broadly. These papers represent the pre-transformer baseline against which later attention-based methods are implicitly compared.

---

## 4. What Do They Predict With That Data?

### 4.1 Three-Dimensional Protein Structure

The primary prediction target for methods like AlphaFold2 and AlphaFold3 is the full atomic three-dimensional structure of a protein, including backbone torsion angles, side-chain conformations, and atomic coordinates (Abbaszadeh & Shahlaee, 2025; Zhang et al., 2025). Accuracy is typically measured in terms of TM-score (template modeling score) and GDT-TS (global distance test) against PDB reference structures. Sanford et al. (2025) predict the same representation but via a continuous-depth ODE-based variant of the Evoformer.

### 4.2 Secondary Structure

Zhou et al. (2024) predict the secondary structure class (alpha-helix, beta-strand, coil) of each residue in a protein sequence. Lin et al. (2016) predict both secondary structure and solvent accessibility per residue. These are residue-level classification tasks evaluated by Q3 or Q8 accuracy (percentage of correctly classified residues).

### 4.3 Protein Fold Class

Han et al. (2022) and Goel et al. (2025) predict the SCOP fold class of an unknown protein sequence, framed as a retrieval (nearest-neighbor in embedding space) or multi-class classification problem over a closed set of known folds.

### 4.4 Protein Stability Change (ΔΔG)

Pak et al. (2023), Barducci et al. (2026), and Xu et al. (2025) predict the change in folding free energy (ΔΔG, in kcal/mol) caused by a single point mutation. Positive ΔΔG indicates destabilization; negative ΔΔG indicates stabilization. This is evaluated by Pearson correlation and root-mean-squared error (RMSE) against experimental calorimetric measurements.

### 4.5 Residue-Level Contact Maps

Chen et al. (2020) predict binary contact maps: for each pair of residues (i, j) in a protein, whether their Cβ atoms are within 8 Å in the native structure. Precision at the top-L/5 predicted contacts (where L is sequence length) is the primary evaluation metric. Contact prediction is an intermediate step toward full 3D structure prediction.

### 4.6 Protein-Protein Interaction Sites

Fu et al. (2024) and Animesh et al. (2024) predict, at the residue level, which amino acids on a protein surface participate in protein-protein interactions. This is a binary classification per residue, evaluated by AUC, precision, recall, and F1-score.

### 4.7 Phosphorylation Site Function

Zhang et al. (2024) predict whether an identified phosphorylation site is functionally important (i.e., participates in regulatory signaling) rather than merely present. This is a binary classification at the PTM site level.

### 4.8 Protein Loop Conformations

Wang et al. (2023) predict the full atomic coordinates of protein loop regions (segments of 4–20 residues in length), with accuracy evaluated by RMSD to crystallographic ground truth at both backbone and all-atom levels.

### 4.9 HP Model Conformation Energy

Liu & Iba (2025) and Yang et al. (2022) predict (or learn to construct) conformations on 2D/3D lattices that maximize H-H contacts, approximating the minimum-energy fold for the HP model. The evaluation metric is the number of H-H contacts achieved relative to the known optimum.

### 4.10 Protein-DNA Binding Residues

Song et al. (2024) predict residues involved in DNA binding, formulated as residue-level binary classification.

### 4.11 Alternative Folds and Conformational Heterogeneity

Chakravarty et al. (2024) do not make new predictions but systematically evaluate AlphaFold's failures on "metamorphic" proteins — proteins with multiple stable native conformations — demonstrating that confidence scores (pLDDT) are inadequate predictors of structural accuracy for this class of proteins.

### 4.12 Topological Features (Knots)

Brems et al. (2022) and Jahagirdar (2024) predict or analyze the knotting complexity of protein backbone traces, using topological invariants (Alexander polynomial, knot group). These are not learned predictions but algorithmic analyses of AlphaFold outputs.

---

## 5. Causation vs. Correlation

This section explicitly distinguishes causal claims from correlational observations in the corpus, following the mandate to avoid conflating association with mechanism.

### 5.1 Correlational Findings

**Attention weights and evolutionary covariation.** Chen et al. (2020) report that attention heads in their contact prediction network learn weights that correlate with coevolutionary signals in MSAs (e.g., direct coupling analysis scores). This is a correlational observation: the attention weights co-vary with coevolutionary statistics, but the authors do not establish that the attention mechanism *causes* improved contact prediction via this mechanism — alternative explanations (e.g., attention learning sequence motifs unrelated to coevolution) are not ruled out.

**Transformer depth and prediction accuracy.** Abbaszadeh & Shahlaee (2025) and Zhang et al. (2025) assert that deeper transformer architectures (more Evoformer blocks) correlate with higher prediction accuracy, but architectural depth is confounded with model size, training data, and training compute. The relationship is correlational absent controlled ablations that vary only depth.

**pLDDT and structural accuracy.** Chakravarty et al. (2024) demonstrate that AlphaFold's per-residue confidence score (pLDDT) is correlated with accuracy for single-conformation proteins but is not a reliable indicator for proteins with alternative folds. This correlation-versus-accuracy disconnect is an empirical finding, not a mechanistic explanation of why pLDDT fails.

**Evolutionary information and fold prediction performance.** Goel et al. (2025) find that incorporating PSSMs alongside raw sequences improves fold recognition accuracy, which is a correlational improvement — the paper does not establish a causal mechanism for which evolutionary signals drive the gains.

**Dataset size and stability prediction performance.** Pak et al. (2023) show that training on a larger aggregated dataset improves ΔΔG prediction correlations with experiment. This is a correlation between dataset size and performance, not a causal demonstration of which data types or distribution shifts are responsible.

### 5.2 Claims Approaching Causal Evidence

**Attention mechanisms vs. no-attention ablations.** Han et al. (2022) perform ablation experiments comparing their attention-augmented CNN with a baseline CNN lacking attention, finding statistically significant improvements in fold recognition accuracy. While ablation studies provide stronger evidence than simple correlations, they do not constitute proof of causality in the mechanistic sense — confounders such as increased parameter count in the attention layer cannot be fully excluded.

**Transformer integration in HP model RL.** Liu & Iba (2025) compare transformer-augmented DQN against CNN-DQN and LSTM-DQN baselines on identical HP benchmark sequences, providing controlled comparisons. The reported improvements in H-H contact scores are more causally attributable to the attention mechanism than purely correlational findings, because the experimental design holds other variables constant. However, the HP model is a severe abstraction of real protein folding physics, limiting generalizability of this causal claim.

**Neural ODE versus discrete Evoformer.** Sanford et al. (2025) compare their continuous-depth Neural ODE variant against the standard 48-block Evoformer on structure prediction benchmarks. If performance is maintained or improved with fewer effective parameters, this provides causal evidence that the rigid layerwise discretization of the Evoformer is not necessary for its representational power. However, the paper is noted as having zero citations at the time of this analysis, and independent replication is absent.

### 5.3 Absence of Causal Evidence

No paper in the corpus provides randomized or interventional causal evidence (e.g., experimental mutagenesis studies directly validating computationally predicted stability effects in a blinded fashion, or protein engineering campaigns that confirm predicted folds in vitro). The gap between computational prediction and experimental validation of causal mechanisms remains a pervasive limitation across the corpus.

---

## 6. Unexplored Areas

Based on systematic analysis of the corpus, the following constitute notable gaps and underexplored directions.

### 6.1 Conformational Dynamics and Ensemble Prediction

AlphaFold and its successors predict a single (or few) static conformation(s), but proteins are dynamic molecules that populate conformational ensembles relevant to function, allostery, and drug binding. Chakravarty et al. (2024) identify alternative fold prediction as a critical blind spot. No paper in the corpus presents a transformer architecture specifically designed to predict thermodynamic ensembles or transition pathways, representing a substantial unmet need.

### 6.2 Mechanistic Interpretability of Attention in Protein Transformers

Chen et al. (2020) make initial progress on interpreting attention in contact prediction, but the internal representations of large transformer models like Evoformer remain poorly understood mechanistically. No paper in the corpus provides rigorous mechanistic interpretability (e.g., circuit-level analysis, probing classifiers for specific structural features) of attention heads in folding-specialized transformers. Given the scientific and engineering importance of understanding model failures, this is a critical gap.

### 6.3 Data-Efficient and Few-Shot Folding Prediction

Beck et al. (2024) address few-shot learning for biophysical property prediction using PLMs, but the specific challenge of data-efficient *folding* prediction — where experimental structural data for a given protein family may be sparse — is not addressed by any architecture paper in the corpus. Most methods implicitly assume access to large labeled datasets.

### 6.4 Multi-Scale Temporal and Kinetic Modeling

The corpus contains no papers that couple transformer architectures with kinetic models of folding (e.g., predicting folding rates, transition state ensembles, or co-translational folding). The energy landscape and kinetic perspective on protein folding (Prentiss et al., 2010; Veitshans et al., 1996; Dokholyan et al., 1998) is entirely absent from the deep learning literature surveyed here, representing a conceptual gap between physics-based and data-driven approaches.

### 6.5 Topologically Complex Proteins

Brems et al. (2022) and Jahagirdar (2024) identify knotted proteins as challenging cases for AlphaFold, but no transformer architecture paper in the corpus is specifically designed to handle topological constraints during structure prediction. Incorporating topological invariants as inductive biases or auxiliary losses into transformer-based folding models is unexplored.

### 6.6 Efficiency and Scalability of Evoformer-Like Architectures

Sanford et al. (2025) identify the computational cost of 48-block Evoformer stacks as a practical bottleneck, and propose Neural ODEs as a partial solution. However, this remains an early-stage proposal (zero citations). Systematic benchmarking of efficiency–accuracy tradeoffs across transformer variants for protein folding is absent from the corpus.

### 6.7 Integration of Experimental Uncertainty

Protein structure determination experiments produce structures with associated error models (B-factors, electron density maps, resolution limitations), but no paper in the corpus incorporates experimental uncertainty quantification into transformer-based prediction. Evidential deep learning approaches (Pandey & Yu, 2023; Pandey et al., 2025) from other domains suggest this is technically feasible but unapplied to protein folding.

### 6.8 Protein Design (Inverse Folding) with Transformers

Wang et al. (2023) describe de novo protein sequence generation using a GAN-based model with attention, but rigorous transformer-based inverse folding — predicting sequences that fold into desired structures — is not represented by any dedicated paper in this corpus. This is a major emerging area not captured by the current survey.

### 6.9 Cross-Modal Learning from Genomic and Proteomic Context

No paper integrates genomic context (gene regulation, co-expression data), organismal phylogeny, or proteome-scale interaction networks as additional modalities in transformer-based folding architectures. The corpus is largely confined to sequence and structure as input modalities.

### 6.10 Benchmarking Against CASP Standards

Critical assessments of transformer architectures using the formalized CASP (Critical Assessment of Structure Prediction) methodology — the gold standard for unbiased evaluation of folding methods — are absent from the corpus. Papers report on their own benchmarks, making cross-paper comparison unreliable.

---

## References

Abbaszadeh, A., & Shahlaee, A. (2025). From Prediction to Simulation: AlphaFold 3 as a Differentiable Framework for Structural Biology. *arXiv*.

Akbar, S., Raza, A., Awan, H. H., et al. (2025). pNPs-CapsNet: Predicting Neuropeptides Using Protein Language Models and FastText Encoding-Based Weighted Multi-View Feature Integration with Deep Capsule Neural Network. *Semantic Scholar*.

Almusallam, N., Shahid, & Hayat, M., et al. (2025). pCPPs-sADNN: predicting cell-penetrating peptides using self-attention based deep neural network. *Semantic Scholar*.

Animesh, R., Suvvada, P. K., Bhowmick, P., et al. (2024). E(Q)AGNN-PPIS: Attention Enhanced Equivariant Graph Neural Network for Protein-Protein Interaction Site Prediction. *Semantic Scholar*.

Barducci, G., Rossi, I., Codicé, F., et al. (2026). JanusDDG: a physics-informed neural network for sequence-based protein stability via two-fronts attention. *Semantic Scholar*.

Beck, J., Surana, S., McAuliffe, M., et al. (2024). Metalic: Meta-Learning In-Context with Protein Language Models. *arXiv*.

Berner, J., Grohs, P., Kutyniok, G., et al. (2021). The Modern Mathematics of Deep Learning. *arXiv*.

Biyu, H., Li, M., Yuxin, H., et al. (2024). A miRNA-disease association prediction model based on tree-path global feature extraction and fully connected artificial neural network with multi-head self-attention mechanism. *Semantic Scholar*.

Brems, M. A., Runkel, R., Yeates, T. O., et al. (2022). AlphaFold predicts the most complex protein knot and composite protein knots. *arXiv*.

Chakravarty, D., Lee, M., & Porter, L. L. (2024). Proteins with alternative folds reveal blind spots in AlphaFold-based protein structure prediction. *arXiv*.

Chen, C., Wu, T., Guo, Z., et al. (2020). Combination of deep neural network with attention mechanism enhances the explainability of protein contact prediction. *Semantic Scholar*.

Chen, Y., Han, L., Zhang, Y., et al. (2024). Inner Product Accelerating Scheme Based on RRAM Array for Attention-Mechanism Neural Network. *Semantic Scholar*.

Coull, S. E., & Gardner, C. (2019). Activation Analysis of a Byte-Based Deep Neural Network for Malware Classification. *arXiv*.

Dai, L.-Y., Mi, C.-L., Wang, X., et al. (2025). MGAMDA: Multi Source Similarity Fusion-Based Graph Convolutional Neural Network and Attention Mechanism Network for Predicting MiRNA-Disease Associations. *Semantic Scholar*.

Das, R. (2012). Atomic-accuracy prediction of protein loop structures through an RNA-inspired ansatz. *arXiv*.

De Ryck, T., Mishra, S., & Ray, D. (2019). On the approximation of rough functions with deep neural networks. *arXiv*.

Deshpande, A., Gupta, D., & Bhurane, A., et al. (2024). Hybrid deep learning-based strategy for the hepatocellular carcinoma cancer grade classification of H&E stained liver histopathology images. *arXiv*.

Dokholyan, N. V., Buldyrev, S. V., Stanley, H. E., et al. (1998). Discrete molecular dynamics studies of the folding of a protein-like model. *arXiv*.

Drori, I., Thaker, D., Srivatsa, A., et al. (2019). Accurate Protein Structure Prediction by Embeddings and Deep Learning Representations. *arXiv*.

Fadhilah, H., Siantika, P., Mulya, D., et al. (2025). Optimalisasi Prediksi Afinitas Interaksi Obat-Target dengan Graph Neural Network dan Attention Mechanism. *Semantic Scholar*.

Fong, I. H., Li, T., Fong, S., et al. (2025). Predicting concentration levels of air pollutants by transfer learning and recurrent neural network. *arXiv*.

Frauenkron, H., Bastolla, U., Gerstner, E., et al. (1998). Testing a New Monte Carlo Strategy for Folding Model Proteins. *arXiv*.

Fu, X., Yuan, Y., Qiu, H., et al. (2024). AGF-PP