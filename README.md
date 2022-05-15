# Accompaniment Generation

The project is using two additional libs:

- MIDO ([https://github.com/mido/mido](https://github.com/mido/mido)). For working with midi files
- Music21 ([https://github.com/cuthbertLab/music21](https://github.com/cuthbertLab/music21)). For determining the key of the melody

### Genetic algorithm

For genetic algorithm I assume that:

- **Individual** is a sequence of chords (for every quarter of beat)
- **Population** is a set of individuals, i.e. set of sequences of chords

Algorithm:

1. First of all, determine the key of the melody (For example, **E# major**)
2. Then, using this key generate population. Each chord in the individual will be generated randomly using notes in determined key.
3. Start evolution algorithm. For each generation:
    1. Using **roulette-wheel select** choose two parents in population. The probability of choosing is computed based on **fitness function.** Each chord in sequence is evaluated:
        - If the chord is constructed correctly(the notes in chord are not neighbors): +1 to overall fit
        - If the chord is constructed in major of minor rule: +2 to overall fit
        - If the chord is suitable with key of note that is playing in corresponding quarter of beat: +3 to overall fit
        - If the chord is suitable with key of melody: +6 to overall fit
    2. **Crossover** them and generate offsprings(take first half of sequence of first one and the second half of the second)
    3. **Mutate** random offspring by making small changed in notes of chord
    4. Repeat *selection, crossover and mutation* 5 times for each generation
    5. Substitute less fit parents with the most fit offsprings

At the end, choose the individual from the obtained population with the maximum values of fitness function and return it as an answer.

The **population size** is equal to 100. The **number of generations** is equal to 100.

We stop when hit max iterations.
