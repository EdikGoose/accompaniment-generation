import mido
from numpy.random import uniform as rand
import numpy as np
from random import randint


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


# Returns population with input size. Population - set of lists of chords
def get_population(population_size: int, melodyTrack):
    return [get_individual(melodyTrack) for _ in range(population_size)]


# Returns level of fitness of chord to input note
# There are three categories in which a chord can fit:
# 1) weak_attr - if the notes in chord are not neighbors
# 2) medium_attr - if the chord is constructed well in one of the rules
# 3) strong_attr - if the chord is suitable with key (тональность) of note
def get_chord_fitness(chord, melody_note):
    weak_attr = 1
    medium_attr = 2
    strong_attr = 3

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

    return chordFitness


# Returns fitness of individual to initial melody
def get_fitness(individual, melodyTrack):
    overallFitness = 0
    notesInTicks = get_notes_in_ticks(melodyTrack)
    for idx in range(0, len(individual)):
        overallFitness += get_chord_fitness(individual[idx], notesInTicks[idx])
    return overallFitness


# Returns fitness of population (sum of individual's fitness)
def get_population_fitness(population, melodyTrack):
    fitness = [get_fitness(individual, melodyTrack) for individual in population]
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
        offsprings[rand_offspring][rand_chord][noteIdx] += randint(-1, 1)

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
def evolution(number_of_generations: int, population_size: int, melodyTrack):
    population = get_population(population_size, melodyTrack)  # create population
    for generation in range(number_of_generations):
        fitness = get_population_fitness(population, melodyTrack)

        offsprings = crossover(population, fitness, 5)
        offsprings = mutate(offsprings)

        offsprings_fitness = get_population_fitness(offsprings, melodyTrack)

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


# Open file
initial_mid = mido.MidiFile('input3.mid')
initial_melody_track = initial_mid.tracks[1]

created_population = evolution(number_of_generations=15, population_size=30, melodyTrack=initial_melody_track)

# Create new midi file
mid = mido.MidiFile()
mid.tracks.append(initial_melody_track)

mid.ticks_per_beat = initial_mid.ticks_per_beat

# Choose the most fitted individual in created population
most_suitable_individual = created_population[0]
for ind in created_population:
    if get_fitness(ind, initial_melody_track) > get_fitness(most_suitable_individual, initial_melody_track):
        most_suitable_individual = ind
mid.tracks.append(create_track(most_suitable_individual, initial_melody_track))

mid.save('output.mid')
