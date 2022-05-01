import mido
from numpy.random import uniform as rand
import numpy as np
from random import randint

initial_mid = mido.MidiFile('input1.mid')
melodyTrack = initial_mid.tracks[1]


def open_chord(time, track, note1, note2, note3):
    track.append(mido.Message('note_on', channel=0, note=note1, velocity=50, time=time))
    track.append(mido.Message('note_on', channel=0, note=note2, velocity=50, time=0))
    track.append(mido.Message('note_on', channel=0, note=note3, velocity=50, time=0))


def close_chord(time, track, note1, note2, note3):
    track.append(mido.Message('note_off', channel=0, note=note1, velocity=0, time=time))
    track.append(mido.Message('note_off', channel=0, note=note2, velocity=0, time=0))
    track.append(mido.Message('note_off', channel=0, note=note3, velocity=0, time=0))


def get_time_of_melody(melodyTrack):
    timeOfMelody = 0
    for msg in melodyTrack:
        timeOfMelody += msg.time
    return timeOfMelody


# For each quarter beat we set respective note
def get_notes_in_ticks(melodyTrack):
    timeOfMelody = get_time_of_melody(melodyTrack)
    ticks = initial_mid.ticks_per_beat
    notes = []
    for i in range(0, timeOfMelody + 1, ticks):
        notes.append(0)

    currentTime = 0
    for msg in melodyTrack:
        currentTime += msg.time
        if msg.type == 'note_on' and notes[currentTime // ticks] == 0:
            notes[currentTime // ticks] = msg.note

    return notes


def get_individual(melodyTrack):
    timeOfMelody = get_time_of_melody(melodyTrack)
    notesInTicks = get_notes_in_ticks(melodyTrack)
    chords = []

    previousNote = [40, 44, 47]

    # note - note in respective quarter of byte
    for numberOfQuart, note in enumerate(notesInTicks):
        if note == 0:
            chords.append(previousNote)
            continue

        listOfNotes = []
        for i in range(3):
            listOfNotes.append(int((note - 24) + randint(-7, 7)))

        # note1 = int(note * rand(0.2, 0.9))
        # note2 = int(note * rand(0.2, 0.9))
        # note3 = int(note * rand(0.2, 0.9))

        # listOfNotes = [note1, note2, note3]
        listOfNotes.sort()
        previousNote = listOfNotes
        chords.append(listOfNotes)
    return chords


def create_track(chords, melodyTrack):
    chordsTrack = mido.MidiTrack()
    ticks = initial_mid.ticks_per_beat

    chordsTrack.append(melodyTrack[0])
    chordsTrack.append(melodyTrack[1])

    for chord in chords:
        if (chord[0] < 0 or chord[1] < 0 or chord[2] < 0):
            continue
        open_chord(0, chordsTrack, chord[0], chord[1], chord[2])
        close_chord(ticks, chordsTrack, chord[0], chord[1], chord[2])
    return chordsTrack


def get_chord_fitness(chord, melody_note):
    weakAttr = 1
    mediumAttr = 2
    strongAttr = 3

    chordFitness = 0

    if chord[1] - chord[0] > 1:
        chordFitness += weakAttr
    if chord[2] - chord[1] > 1:
        chordFitness += weakAttr

    if chord[1] - chord[0] == 3 and chord[2] - chord[1] == 4:
        chordFitness += mediumAttr
    if chord[1] - chord[0] == 4 and chord[2] - chord[1] == 3:
        chordFitness += mediumAttr

    temp_note = melody_note - 24
    major = [temp_note, temp_note + 2, temp_note + 2, temp_note + 1, temp_note + 2, temp_note + 2, temp_note + 2,
             temp_note + 1]
    minor = [temp_note, temp_note + 2, temp_note + 1, temp_note + 2, temp_note + 2, temp_note + 1, temp_note + 2,
             temp_note + 2]

    for chord_note in chord:
        if chord_note in minor or chord_note in major:
            chordFitness += strongAttr

    return chordFitness


def get_fitness(individual):
    overallFitness = 0
    notesInTicks = get_notes_in_ticks(melodyTrack)
    for idx in range(0, len(individual)):
        overallFitness += get_chord_fitness(individual[idx], notesInTicks[idx])
    return overallFitness


def get_population(population_size: int):
    return [get_individual(melodyTrack) for i in range(population_size)]


def population_fitness(population):
    fitness = [get_fitness(individual) for individual in population]
    return (fitness, np.mean(fitness))


def roulette_wheel_select(fitness):
    selection_probs = [current_fitness / sum(fitness) for current_fitness in fitness]
    return np.random.choice(range(len(fitness)), 1, p=selection_probs)[0]


def crossover(population, fitness, size):
    offsprings = []
    for i in range(size):
        idx1, idx2 = roulette_wheel_select(fitness), roulette_wheel_select(fitness)
        parent1, parent2 = population[idx1], population[idx2]
        offspring = []
        for i in range(len(parent1)):
            if (i > len(parent1) // 2):
                offspring.append(parent2[i])
            else:
                offspring.append(parent1[i])

        offsprings.append(offspring)
    return offsprings


def mutate(offsprings):
    rand_offspring = randint(0, len(offsprings) - 1)
    rand_chord = randint(0, len(offsprings[0]) - 1)

    for noteIdx in range(3):
        offsprings[rand_offspring][rand_chord][noteIdx] += randint(-1, 1)

    return offsprings


def replace_parents(population, population_fitness, offsprings, offsprings_fitness, size: int):
    n = len(population_fitness)
    for i in range(n - 1):
        for j in range(0, n - i - 1):
            if population_fitness[j] > population_fitness[j + 1]:
                population[j], population[j + 1] = population[j + 1], population[j]
                population_fitness[j], population_fitness[j + 1] = population_fitness[j + 1], population_fitness[j]

    n = len(offsprings_fitness)
    for i in range(n - 1):
        for j in range(0, n - i - 1):
            if population_fitness[j] < population_fitness[j + 1]:
                offsprings[j], offsprings[j + 1] = offsprings[j + 1], offsprings[j]
                offsprings_fitness[j], offsprings_fitness[j + 1] = offsprings_fitness[j + 1], offsprings_fitness[j]

    for i in range(size):
        population[i] = offsprings[i]

    return population


def evolution(generations: int, population_size: int):
    population = get_population(population_size)
    for generation in range(generations):
        fitness, avg = population_fitness(population)

        offsprings = crossover(population, fitness, 5)
        offsprings = mutate(offsprings)

        offsprings_fitness, avg_offspr = population_fitness(offsprings)

        population = replace_parents(population, fitness, offsprings, offsprings_fitness, 3)
    return population


population = evolution(generations=500, population_size=30)

mid = mido.MidiFile()
mid.tracks.append(melodyTrack)

mid.ticks_per_beat = initial_mid.ticks_per_beat

most_suitable_individual = population[0]
for ind in population:
    if get_fitness(ind) > get_fitness(most_suitable_individual):
        most_suitable_individual = ind
mid.tracks.append(create_track(most_suitable_individual, melodyTrack))

mid.save('new_song.mid')
