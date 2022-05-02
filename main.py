import copy

import mido
from numpy.random import uniform as rand
import numpy as np
from random import randint
import music21


# Returns the time of the whole melody.
def get_time_of_melody(melodyTrack):
    timeOfMelody = 0
    for msg in melodyTrack:
        timeOfMelody += msg.time
    return timeOfMelody


# Returns list of notes for each respective quarter beat
# If there are many notes in the quarter, returns the first one
def get_notes_in_ticks(melodyTrack):
    timeOfMelody = get_time_of_melody(melodyTrack)
    ticks = initial_mid.ticks_per_beat
    notes = []

    for i in range(0, timeOfMelody + 1, ticks):
        notes.append(0)

    currentTime = 0
    for msg in melodyTrack:
        currentTime += msg.time
        # currentTime // ticks = number of quarter
        if msg.type == 'note_on' and notes[currentTime // ticks] == 0:
            notes[currentTime // ticks] = msg.note

    return notes


# Returns list with chords in each quarter beat
def get_individual(melodyTrack):
    notesInTicks = get_notes_in_ticks(melodyTrack)
    chords = []

    previousNote = [60, 64, 67]

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


# Returns population with input size. Population - set of lists of chords
def get_population(population_size: int, melodyTrack):
    return [get_individual(melodyTrack) for _ in range(population_size)]


# Returns level of fitness of chord to input note
# There are three categories in which a chord can fit:
# 1) weak_attr - if the notes in chord are not neighbors
# 2) medium_attr - if the chord is constructed well in one of the rules
# 3) strong_attr - if the chord is suitable with key (тональность) of note
def get_chord_fitness(chord, melody_note, key):
    weak_attr = 1
    medium_attr = 2
    strong_attr = 3
    best_attr = 100

    chordFitness = 0

    if chord[1] - chord[0] > 1:
        chordFitness += weak_attr
    if chord[2] - chord[1] > 1:
        chordFitness += weak_attr

    if chord[1] - chord[0] == 3 and chord[2] - chord[1] == 4:
        chordFitness += medium_attr
    if chord[1] - chord[0] == 4 and chord[2] - chord[1] == 3:
        chordFitness += medium_attr

    temp_note = melody_note - 24
    major = [temp_note, temp_note + 2, temp_note + 2, temp_note + 1, temp_note + 2, temp_note + 2, temp_note + 2,
             temp_note + 1]
    minor = [temp_note, temp_note + 2, temp_note + 1, temp_note + 2, temp_note + 2, temp_note + 1, temp_note + 2,
             temp_note + 2]

    for chord_note in chord:
        if chord_note in minor or chord_note in major:
            chordFitness += strong_attr

    for chord_note in chord:
        if chord_note in key:
            chordFitness += best_attr

    return chordFitness


# Returns fitness of individual to initial melody
def get_fitness(individual, melodyTrack, key):
    overallFitness = 0
    notesInTicks = get_notes_in_ticks(melodyTrack)
    for idx in range(0, len(individual)):
        overallFitness += get_chord_fitness(individual[idx], notesInTicks[idx], key)
    return overallFitness


# Returns fitness of population (sum of individual's fitness)
def get_population_fitness(population, melodyTrack, key):
    fitness = [get_fitness(individual, melodyTrack, key) for individual in population]
    return fitness


# Returns random index of individual in population. Probability is dependent on fitness of individuals
def roulette_wheel_select(fitness):
    selection_probs = [current_fitness / sum(fitness) for current_fitness in fitness]
    return np.random.choice(range(len(fitness)), 1, p=selection_probs)[0]


# Crossover two roulette wheel selected individuals in population.
# Takes first half of first one and the second half of the another.
def crossover(population, fitness, size):
    offsprings = []
    for i in range(size):
        idx1, idx2 = roulette_wheel_select(fitness), roulette_wheel_select(fitness)
        parent1, parent2 = population[idx1], population[idx2]
        offspring = []
        for index_of_parent in range(len(parent1)):
            if index_of_parent > len(parent1) // 2:
                offspring.append(parent2[index_of_parent])
            else:
                offspring.append(parent1[index_of_parent])
        offsprings.append(offspring)
    return offsprings


# Takes random individual in offspring and random chord. Then randomly changes notes in chord
def mutate(offsprings):
    rand_offspring = randint(0, len(offsprings) - 1)
    rand_chord = randint(0, len(offsprings[0]) - 1)

    for noteIdx in range(3):
        offsprings[rand_offspring][rand_chord][noteIdx] += randint(-2, 5)

    return offsprings


# Replace number_of_replaced the least fit parents in population by most fit offsprings
def replace_parents(population, population_fitness, offsprings, offsprings_fitness, number_of_replaced: int):
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

    for i in range(number_of_replaced):
        population[i] = offsprings[i]

    return population


# Make number_of_generations crossovers and mutations for created population with input size
def evolution(number_of_generations: int, population, melodyTrack, key):
    for generation in range(number_of_generations):
        fitness = get_population_fitness(population, melodyTrack, key)

        offsprings = crossover(population, fitness, 5)
        offsprings = mutate(offsprings)

        offsprings_fitness = get_population_fitness(offsprings, melodyTrack, key)

        population = replace_parents(population, fitness, offsprings, offsprings_fitness, 3)
    return population


# Add "note_on" messages for input 3 notes(chord) to input track
def open_chord(time, track, note1, note2, note3):
    track.append(mido.Message('note_on', channel=0, note=note1, velocity=50, time=time))
    track.append(mido.Message('note_on', channel=0, note=note2, velocity=50, time=0))
    track.append(mido.Message('note_on', channel=0, note=note3, velocity=50, time=0))


# Add "note_off" messages for input 3 notes(chord) to input track
def close_chord(time, track, note1, note2, note3):
    track.append(mido.Message('note_off', channel=0, note=note1, velocity=0, time=time))
    track.append(mido.Message('note_off', channel=0, note=note2, velocity=0, time=0))
    track.append(mido.Message('note_off', channel=0, note=note3, velocity=0, time=0))


# For input list of chords, create track for midi file
def create_track(chords, melodyTrack):
    chordsTrack = mido.MidiTrack()
    ticks = initial_mid.ticks_per_beat

    chordsTrack.append(melodyTrack[0])
    chordsTrack.append(melodyTrack[1])

    for chord in chords:
        if chord[0] < 0 or chord[1] < 0 or chord[2] < 0:
            continue
        open_chord(0, chordsTrack, chord[0], chord[1], chord[2])
        close_chord(ticks, chordsTrack, chord[0], chord[1], chord[2])
    return chordsTrack


def get_key(fileName, min_note):
    score = music21.converter.parse(fileName)
    key = score.analyze('key')

    note = music21.note.Note(key.tonic.name)
    notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    octave = min_note // 12
    first_note = (octave - 2) * 12 + notes[note.name]
    if key.mode == 'minor':
        key = [first_note, first_note + 2, first_note + 3, first_note + 5, first_note + 7, first_note + 8,
               first_note + 10, first_note + 12]
    else:
        key = [first_note, first_note + 2, first_note + 4, first_note + 5, first_note + 7, first_note + 9,
               first_note + 11, first_note + 12]
    return key


# Open file
fileName = 'input1.mid'

initial_mid = mido.MidiFile(fileName)
initial_melody_track = initial_mid.tracks[1]

min_note = 200
for msg in initial_melody_track:
    if msg.type == 'note_on':
        if msg.note < min_note:
            min_note = msg.note

current_key = get_key(fileName, min_note)
print(current_key)

# created_population = get_population(population_size=30, melodyTrack=initial_melody_track)
created_population = [[[38, 48, 50], [48, 50, 50], [40, 41, 45], [37, 41, 42], [39, 41, 44], [38, 39, 47], [38, 42, 48], [36, 38, 46], [37, 38, 43], [37, 43, 45], [35, 36, 39], [35, 37, 44], [34, 40, 47], [38, 40, 42], [47, 47, 50], [39, 43, 48], [38, 41, 48], [39, 45, 50], [40, 47, 50], [45, 45, 49], [36, 38, 46], [33, 41, 44], [33, 39, 40], [38, 41, 50], [46, 47, 49], [42, 44, 50], [35, 39, 48], [33, 35, 37], [34, 45, 46], [32, 43, 44]], [[41, 44, 49], [38, 40, 49], [36, 43, 47], [32, 37, 43], [42, 44, 44], [40, 42, 50], [46, 47, 49], [42, 49, 49], [39, 40, 44], [36, 38, 38], [40, 44, 46], [33, 35, 35], [35, 41, 45], [37, 47, 48], [43, 46, 48], [44, 50, 51], [37, 48, 48], [41, 44, 45], [39, 42, 48], [36, 45, 46], [36, 41, 45], [31, 34, 39], [33, 43, 45], [39, 44, 44], [37, 41, 43], [38, 39, 41], [39, 43, 48], [36, 36, 38], [39, 42, 42], [33, 34, 44]], [[40, 44, 49], [41, 49, 49], [36, 43, 46], [35, 39, 43], [42, 44, 45], [39, 40, 40], [38, 39, 44], [36, 38, 49], [36, 41, 45], [34, 42, 43], [33, 38, 41], [31, 32, 42], [35, 42, 47], [37, 42, 47], [42, 45, 49], [41, 41, 51], [42, 46, 46], [42, 50, 51], [43, 47, 50], [39, 40, 50], [41, 44, 48], [32, 40, 43], [32, 36, 41], [41, 42, 46], [38, 47, 48], [46, 46, 47], [34, 34, 40], [32, 34, 42], [41, 44, 45], [38, 39, 42]], [[36, 40, 50], [40, 41, 47], [39, 41, 44], [35, 40, 42], [36, 38, 38], [37, 42, 46], [40, 44, 48], [36, 39, 42], [38, 46, 46], [32, 33, 40], [33, 42, 44], [34, 39, 45], [33, 42, 44], [36, 36, 37], [40, 51, 52], [44, 44, 50], [42, 44, 49], [40, 47, 49], [39, 43, 47], [39, 49, 50], [41, 46, 48], [36, 40, 45], [33, 37, 45], [49, 49, 50], [41, 43, 47], [42, 43, 48], [35, 37, 42], [38, 38, 45], [35, 37, 47], [35, 40, 44]], [[36, 39, 46], [36, 38, 40], [34, 40, 48], [37, 39, 42], [36, 40, 41], [39, 42, 47], [39, 48, 49], [39, 45, 49], [39, 46, 48], [43, 43, 44], [33, 39, 45], [31, 33, 40], [39, 41, 45], [36, 36, 43], [42, 49, 51], [38, 47, 49], [39, 42, 43], [40, 47, 51], [41, 43, 49], [37, 41, 50], [35, 38, 43], [31, 36, 38], [31, 38, 41], [41, 46, 50], [36, 48, 49], [45, 48, 50], [34, 36, 37], [37, 38, 41], [38, 41, 41], [35, 39, 40]], [[39, 46, 48], [36, 41, 45], [34, 42, 47], [31, 38, 45], [34, 35, 41], [42, 46, 49], [44, 46, 50], [37, 41, 43], [37, 38, 43], [34, 40, 45], [33, 36, 42], [32, 34, 36], [35, 43, 44], [37, 43, 47], [39, 44, 47], [45, 47, 49], [40, 44, 49], [38, 40, 47], [48, 49, 49], [36, 36, 46], [39, 42, 46], [37, 38, 41], [36, 39, 41], [37, 43, 47], [36, 40, 43], [36, 37, 38], [39, 41, 44], [31, 32, 34], [42, 44, 44], [33, 34, 41]], [[36, 43, 43], [40, 43, 47], [35, 40, 47], [33, 36, 39], [31, 33, 39], [36, 39, 47], [36, 37, 49], [36, 38, 45], [36, 36, 46], [36, 38, 41], [33, 40, 43], [32, 41, 42], [35, 43, 44], [35, 38, 44], [42, 46, 50], [41, 42, 42], [38, 38, 50], [38, 42, 50], [36, 41, 45], [42, 48, 49], [40, 41, 43], [37, 40, 43], [33, 41, 43], [39, 39, 43], [38, 42, 48], [38, 40, 50], [41, 44, 46], [35, 35, 39], [33, 34, 37], [31, 32, 39]], [[36, 40, 48], [36, 40, 47], [38, 39, 42], [39, 44, 45], [35, 40, 43], [36, 43, 50], [37, 41, 45], [46, 47, 50], [41, 42, 47], [33, 33, 36], [38, 42, 45], [31, 33, 43], [42, 43, 43], [34, 46, 48], [42, 42, 43], [41, 46, 48], [38, 43, 44], [47, 50, 50], [37, 41, 45], [37, 41, 50], [41, 47, 48], [32, 40, 44], [36, 38, 41], [36, 38, 44], [39, 39, 50], [45, 46, 49], [35, 36, 39], [32, 37, 41], [34, 43, 45], [32, 42, 45]], [[39, 42, 47], [38, 45, 45], [36, 40, 44], [32, 34, 35], [38, 40, 43], [44, 48, 50], [36, 41, 49], [38, 42, 44], [38, 43, 44], [33, 34, 36], [34, 34, 47], [35, 40, 41], [34, 46, 47], [40, 44, 47], [43, 46, 52], [46, 46, 47], [46, 46, 47], [44, 49, 50], [36, 39, 45], [38, 48, 50], [34, 37, 46], [37, 38, 38], [36, 37, 45], [38, 45, 46], [37, 38, 50], [38, 40, 45], [41, 42, 47], [33, 37, 43], [37, 37, 41], [38, 43, 44]], [[39, 45, 49], [41, 46, 47], [35, 38, 41], [33, 38, 44], [31, 37, 43], [43, 45, 48], [38, 45, 45], [40, 40, 41], [39, 40, 45], [34, 40, 43], [33, 39, 43], [31, 38, 42], [36, 43, 45], [37, 41, 46], [38, 40, 51], [43, 49, 52], [44, 44, 50], [42, 43, 52], [36, 40, 50], [41, 43, 43], [38, 43, 45], [37, 42, 42], [31, 32, 41], [38, 43, 46], [40, 47, 49], [40, 45, 49], [34, 37, 48], [32, 34, 38], [36, 38, 47], [34, 36, 39]], [[41, 46, 49], [40, 47, 49], [36, 47, 48], [31, 37, 40], [38, 43, 43], [36, 46, 50], [36, 40, 48], [40, 41, 48], [42, 43, 48], [35, 35, 44], [34, 43, 46], [38, 40, 45], [35, 41, 41], [35, 41, 46], [39, 50, 51], [45, 47, 48], [37, 38, 49], [41, 42, 51], [37, 39, 39], [40, 45, 49], [43, 44, 45], [32, 37, 45], [33, 34, 40], [44, 45, 46], [40, 47, 49], [37, 45, 46], [35, 37, 48], [32, 37, 40], [33, 37, 40], [31, 40, 42]], [[39, 39, 43], [39, 41, 41], [34, 42, 45], [32, 36, 38], [37, 41, 44], [36, 42, 48], [42, 50, 50], [40, 47, 47], [37, 41, 46], [33, 37, 44], [43, 43, 47], [37, 42, 45], [33, 36, 37], [36, 39, 46], [41, 45, 46], [41, 45, 48], [36, 43, 44], [41, 42, 44], [36, 43, 50], [45, 46, 50], [34, 39, 43], [34, 44, 44], [33, 33, 36], [36, 43, 44], [37, 44, 47], [38, 40, 40], [38, 46, 47], [32, 43, 44], [33, 35, 39], [32, 33, 38]], [[39, 47, 48], [39, 43, 50], [36, 39, 44], [35, 41, 41], [31, 39, 43], [38, 41, 45], [41, 41, 42], [38, 42, 50], [37, 43, 47], [39, 43, 43], [35, 43, 45], [36, 45, 45], [34, 45, 45], [39, 41, 43], [43, 51, 51], [40, 50, 51], [44, 50, 50], [39, 40, 47], [37, 39, 46], [39, 47, 47], [36, 38, 41], [31, 34, 45], [31, 35, 44], [37, 42, 49], [38, 39, 40], [37, 42, 47], [35, 39, 46], [31, 34, 34], [40, 42, 44], [33, 42, 45]], [[37, 38, 44], [37, 38, 46], [36, 38, 47], [31, 34, 43], [33, 34, 37], [37, 41, 44], [36, 37, 46], [36, 41, 44], [37, 43, 47], [33, 39, 42], [41, 44, 46], [35, 37, 42], [35, 42, 43], [35, 37, 46], [39, 45, 47], [38, 45, 49], [37, 40, 43], [46, 46, 51], [38, 42, 44], [38, 41, 49], [34, 34, 36], [34, 43, 45], [32, 36, 37], [39, 44, 46], [46, 47, 48], [37, 38, 42], [34, 38, 39], [31, 35, 39], [36, 39, 39], [37, 41, 43]], [[41, 46, 49], [42, 45, 46], [37, 41, 45], [33, 33, 34], [41, 44, 45], [40, 42, 49], [39, 43, 45], [36, 38, 39], [37, 38, 46], [32, 33, 34], [37, 37, 38], [33, 35, 44], [40, 41, 43], [37, 42, 46], [42, 43, 46], [41, 46, 50], [43, 45, 50], [38, 42, 42], [37, 40, 45], [36, 36, 43], [39, 46, 48], [35, 37, 38], [35, 38, 45], [38, 40, 47], [38, 41, 49], [36, 40, 47], [35, 45, 46], [33, 39, 39], [39, 40, 43], [34, 40, 42]], [[41, 44, 49], [43, 47, 47], [34, 38, 47], [32, 40, 45], [36, 39, 40], [36, 37, 46], [36, 49, 50], [40, 44, 49], [37, 38, 43], [37, 40, 45], [36, 38, 45], [35, 38, 43], [36, 38, 45], [39, 43, 44], [38, 41, 46], [44, 47, 48], [43, 44, 48], [38, 39, 40], [38, 50, 50], [37, 42, 47], [37, 42, 47], [33, 34, 40], [33, 33, 38], [38, 40, 44], [45, 47, 48], [36, 37, 39], [37, 39, 45], [32, 38, 38], [36, 44, 45], [34, 35, 38]], [[36, 41, 47], [38, 39, 45], [37, 37, 37], [31, 41, 45], [32, 40, 41], [41, 42, 49], [41, 42, 43], [40, 45, 46], [35, 37, 40], [31, 34, 34], [38, 38, 43], [38, 40, 43], [37, 39, 47], [35, 39, 46], [40, 50, 52], [39, 40, 41], [38, 47, 48], [41, 49, 52], [41, 43, 45], [36, 40, 48], [34, 38, 41], [33, 36, 41], [32, 38, 39], [45, 47, 50], [36, 40, 50], [37, 41, 43], [34, 35, 41], [31, 32, 45], [34, 40, 42], [33, 39, 44]], [[45, 46, 50], [37, 39, 41], [35, 42, 43], [35, 38, 40], [35, 40, 40], [45, 47, 47], [37, 42, 43], [39, 43, 46], [37, 47, 48], [32, 34, 35], [34, 41, 42], [36, 43, 44], [33, 34, 45], [40, 41, 44], [39, 49, 51], [41, 49, 49], [42, 46, 47], [43, 47, 52], [37, 40, 48], [36, 37, 45], [37, 37, 43], [32, 33, 37], [34, 36, 36], [36, 44, 44], [40, 45, 49], [46, 48, 50], [34, 41, 44], [32, 36, 40], [35, 45, 47], [32, 36, 42]], [[41, 49, 49], [42, 45, 46], [35, 46, 48], [33, 34, 34], [33, 38, 44], [36, 39, 44], [45, 46, 46], [37, 42, 46], [35, 37, 41], [33, 35, 45], [33, 39, 45], [33, 34, 37], [36, 40, 47], [35, 37, 41], [38, 45, 52], [40, 43, 46], [38, 38, 41], [38, 44, 50], [39, 39, 47], [42, 47, 50], [40, 43, 44], [31, 36, 38], [35, 37, 41], [42, 46, 49], [36, 48, 50], [46, 47, 49], [36, 43, 45], [37, 40, 43], [38, 40, 43], [31, 34, 41]], [[36, 37, 50], [46, 49, 49], [39, 39, 42], [36, 40, 45], [40, 42, 42], [36, 36, 37], [38, 42, 45], [40, 44, 46], [38, 45, 48], [31, 40, 44], [40, 42, 43], [33, 43, 45], [40, 45, 46], [35, 37, 42], [40, 43, 44], [39, 40, 44], [39, 41, 47], [40, 51, 52], [42, 44, 45], [39, 44, 45], [35, 39, 45], [37, 42, 42], [33, 35, 45], [40, 47, 47], [37, 40, 49], [40, 44, 50], [37, 41, 44], [31, 35, 36], [33, 35, 39], [37, 39, 40]], [[41, 46, 47], [38, 42, 46], [37, 45, 45], [35, 36, 36], [38, 40, 42], [40, 43, 48], [37, 48, 49], [38, 43, 44], [35, 42, 43], [33, 34, 34], [33, 33, 43], [35, 38, 44], [39, 45, 47], [34, 37, 45], [39, 40, 50], [38, 40, 41], [36, 38, 44], [51, 51, 52], [39, 43, 48], [43, 46, 50], [34, 35, 42], [35, 36, 42], [31, 39, 43], [43, 49, 50], [38, 41, 44], [38, 39, 45], [34, 34, 48], [32, 38, 45], [37, 39, 47], [36, 37, 38]], [[36, 41, 45], [37, 40, 46], [34, 36, 45], [34, 36, 41], [32, 38, 41], [40, 41, 45], [36, 41, 46], [38, 48, 49], [36, 42, 43], [31, 32, 36], [34, 37, 42], [36, 38, 40], [43, 45, 46], [34, 34, 48], [39, 40, 43], [38, 40, 49], [39, 43, 45], [39, 45, 52], [36, 37, 41], [37, 45, 50], [37, 37, 45], [33, 39, 41], [35, 35, 44], [39, 45, 50], [43, 48, 49], [37, 45, 48], [34, 38, 39], [32, 33, 42], [35, 37, 45], [31, 38, 39]], [[36, 36, 44], [42, 47, 48], [40, 42, 44], [33, 41, 41], [40, 41, 42], [40, 43, 50], [44, 45, 48], [40, 42, 45], [34, 38, 43], [32, 33, 38], [37, 39, 39], [32, 33, 42], [40, 42, 47], [38, 41, 42], [38, 41, 52], [39, 40, 41], [42, 48, 50], [40, 42, 42], [44, 45, 48], [43, 44, 47], [38, 47, 47], [33, 33, 41], [33, 39, 44], [39, 39, 39], [48, 48, 50], [38, 39, 50], [35, 39, 42], [38, 39, 45], [33, 39, 41], [38, 39, 42]], [[36, 45, 47], [44, 46, 46], [34, 42, 44], [34, 36, 41], [32, 33, 40], [36, 40, 42], [39, 47, 48], [36, 46, 47], [34, 44, 44], [31, 41, 44], [33, 37, 44], [34, 36, 41], [38, 39, 47], [37, 38, 40], [39, 46, 50], [43, 43, 46], [36, 40, 45], [44, 46, 50], [41, 44, 46], [36, 37, 44], [38, 39, 44], [36, 40, 41], [33, 42, 43], [40, 43, 43], [42, 45, 47], [40, 42, 47], [39, 44, 47], [31, 36, 40], [33, 35, 37], [36, 37, 40]], [[40, 41, 47], [40, 43, 48], [40, 41, 43], [31, 37, 42], [36, 39, 45], [42, 49, 50], [44, 45, 46], [44, 45, 47], [34, 38, 44], [42, 45, 45], [35, 37, 38], [38, 43, 44], [37, 42, 43], [36, 41, 48], [38, 41, 47], [46, 46, 49], [43, 43, 45], [41, 45, 48], [41, 44, 45], [39, 45, 49], [37, 39, 48], [36, 38, 39], [33, 39, 40], [39, 47, 50], [37, 40, 42], [37, 44, 46], [34, 43, 48], [31, 36, 38], [33, 43, 43], [43, 44, 45]], [[39, 41, 49], [39, 46, 47], [39, 39, 42], [33, 42, 45], [31, 32, 45], [43, 45, 47], [40, 40, 46], [36, 38, 48], [35, 44, 46], [31, 43, 45], [39, 41, 41], [32, 34, 37], [33, 41, 44], [40, 42, 45], [45, 48, 49], [40, 40, 52], [47, 47, 48], [38, 48, 48], [37, 45, 45], [45, 46, 49], [41, 42, 43], [36, 37, 39], [32, 39, 44], [49, 50, 50], [36, 42, 45], [38, 40, 44], [36, 39, 43], [32, 32, 42], [40, 42, 43], [33, 40, 43]], [[40, 47, 50], [36, 37, 48], [38, 44, 44], [31, 33, 40], [31, 33, 45], [39, 40, 49], [48, 49, 50], [41, 41, 47], [34, 37, 48], [31, 31, 32], [36, 38, 39], [34, 43, 44], [36, 39, 42], [36, 39, 47], [45, 50, 50], [39, 43, 43], [39, 41, 45], [39, 40, 52], [43, 47, 50], [46, 48, 49], [40, 45, 47], [38, 40, 45], [35, 37, 39], [39, 49, 50], [39, 40, 41], [39, 48, 49], [36, 39, 44], [33, 41, 42], [38, 39, 41], [39, 44, 45]], [[41, 43, 46], [40, 43, 47], [35, 46, 48], [38, 38, 45], [33, 35, 41], [36, 37, 37], [47, 49, 50], [43, 44, 50], [38, 42, 44], [41, 43, 43], [36, 43, 44], [39, 42, 44], [38, 40, 43], [34, 42, 46], [38, 46, 50], [39, 47, 52], [40, 43, 43], [39, 42, 50], [38, 49, 50], [42, 44, 44], [41, 42, 43], [35, 38, 39], [32, 34, 37], [40, 44, 45], [37, 38, 47], [39, 40, 42], [37, 38, 39], [40, 42, 42], [34, 43, 47], [34, 41, 43]], [[38, 48, 50], [37, 39, 45], [42, 43, 44], [39, 42, 43], [37, 40, 44], [44, 48, 50], [38, 42, 48], [38, 47, 50], [36, 43, 44], [34, 35, 35], [38, 43, 47], [32, 38, 43], [37, 39, 43], [42, 44, 46], [43, 44, 47], [38, 40, 47], [36, 48, 49], [43, 43, 45], [38, 43, 50], [40, 45, 47], [39, 43, 43], [38, 40, 44], [39, 43, 44], [38, 44, 49], [40, 46, 49], [39, 39, 40], [36, 42, 48], [32, 34, 38], [35, 40, 43], [40, 41, 42]], [[37, 43, 44], [39, 42, 49], [36, 37, 47], [31, 35, 36], [32, 41, 44], [36, 36, 47], [38, 43, 49], [37, 43, 46], [38, 45, 48], [41, 41, 43], [38, 44, 47], [43, 44, 44], [36, 36, 37], [41, 47, 48], [41, 42, 50], [38, 52, 52], [36, 45, 49], [38, 39, 49], [37, 38, 48], [36, 36, 42], [36, 43, 47], [35, 38, 39], [34, 36, 40], [36, 37, 38], [36, 42, 49], [43, 46, 50], [41, 43, 48], [36, 42, 44], [33, 41, 44], [36, 39, 41]]]

copy_of_initial_population = copy.deepcopy(created_population)
evolution(number_of_generations=10, population=created_population, melodyTrack=initial_melody_track, key=current_key)

# for i in range(len(created_population)):
#     for j in range(len(created_population[0])):
#         print(copy_of_initial_population[i][j], created_population[i][j])
#     print()

# Create new midi file
mid = mido.MidiFile()
mid.tracks.append(initial_melody_track)

mid.ticks_per_beat = initial_mid.ticks_per_beat

# Choose the most fitted individual in created population
most_suitable_individual = created_population[0]
for ind in created_population:
    if get_fitness(ind, initial_melody_track, current_key) > get_fitness(most_suitable_individual, initial_melody_track, current_key):
        most_suitable_individual = ind
mid.tracks.append(create_track(most_suitable_individual, initial_melody_track))

mid.save('output.mid')
