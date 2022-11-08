# Bachelor Thesis: How blind really is a blind peer review ?
## Simple Count Approach
We assume that the most-cited author is the author them self.
The accuracy might improve using the discriminative approach: a seldom-cited paper might give a better hint about the author

Robustness:
(papers of which authors have published > 1 papers)
relative citation count
institution, country of publication, gender
Exploratory (graph) data analysis

### Features:

- aggregate and count number of authors' names
- Discrimative: references' citation count / maybe h-index

### Labels:
- authors' name

### Open Questions:
- What does "largest number of citations" mean?

## Characteristic Vector Classifier
Given a depth d, we could create a characteristic vector for each paper/author, perform a graph traversal for a new input and classify it using the cosine similarity

### Features:
- depht d references' authors/papers as vectors
- (discriminative approach e.g. referenceCount, h-index)?

### Labels:
- author

## Random Walk Classifier
Assuming that authors write about similar topics, this could motivate the Random Walk as probabilistic approach

1. Repeat the following 10, 000 times:
2. Pick a random paper r that P cites.
3. Pick a random paper s that cites r (excluding P).
4. Let r = s. With probability 2/3, HALT and add probability mass to each author
of r. with probability 1/3, go to step 3.

### (Distributed) Graph Neural Network

### Features:
- Vector of authors
- (Vector of papers)
- (h - index as weight?)

### Labels:
- author

### General Questions:
- Is it feasible to extract the institution/country/gender?