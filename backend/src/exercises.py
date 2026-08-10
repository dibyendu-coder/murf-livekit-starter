"""
exercises.py — Local Learning Exercise Dataset and evaluation logic.

Provides two public functions used by the voice agent's @function_tool methods:
  - get_next_exercise() : retrieve a suitable exercise from the dataset
  - evaluate_answer()   : evaluate a learner's answer for a given exercise

Dataset source  : Local Learning Exercise Dataset (locally curated)
Data version    : 2026-08-10
Exercises       : 35 exercises across beginner / intermediate / advanced levels,
                  covering grammar, vocabulary, sentence_formation, speaking,
                  and comprehension skills.
"""

import logging
import random
import re
from typing import Any

logger = logging.getLogger("exercises")

# ---------------------------------------------------------------------------
# Dataset metadata
# ---------------------------------------------------------------------------

DATASET_SOURCE = "Local Learning Exercise Dataset"
DATA_VERSION = "2026-08-10"

# ---------------------------------------------------------------------------
# Exercise dataset — 35 exercises
# ---------------------------------------------------------------------------

EXERCISES: list[dict[str, Any]] = [
    # ── GRAMMAR – BEGINNER ────────────────────────────────────────────────
    {
        "id": "grammar_001",
        "level": "beginner",
        "skill": "grammar",
        "topic": "present tense",
        "question": "She ___ to school every day.",
        "options": ["go", "goes", "going"],
        "correct_answer": "goes",
        "explanation": "We use 'goes' with 'she' in the simple present tense.",
        "difficulty": 1,
        "exercise_type": "fill_in_the_blank",
    },
    {
        "id": "grammar_002",
        "level": "beginner",
        "skill": "grammar",
        "topic": "articles",
        "question": "I have ___ apple in my bag.",
        "options": ["a", "an", "the"],
        "correct_answer": "an",
        "explanation": "'An' is used before words that begin with a vowel sound, like 'apple'.",
        "difficulty": 1,
        "exercise_type": "fill_in_the_blank",
    },
    {
        "id": "grammar_003",
        "level": "beginner",
        "skill": "grammar",
        "topic": "plural nouns",
        "question": "There are three ___ in the park.",
        "options": ["child", "childs", "children"],
        "correct_answer": "children",
        "explanation": "The plural of 'child' is 'children', an irregular plural form.",
        "difficulty": 1,
        "exercise_type": "multiple_choice",
    },
    {
        "id": "grammar_004",
        "level": "beginner",
        "skill": "grammar",
        "topic": "past tense",
        "question": "Yesterday, he ___ a letter to his friend.",
        "options": ["write", "wrote", "written"],
        "correct_answer": "wrote",
        "explanation": "'Wrote' is the simple past tense of 'write'.",
        "difficulty": 1,
        "exercise_type": "multiple_choice",
    },
    {
        "id": "grammar_005",
        "level": "beginner",
        "skill": "grammar",
        "topic": "pronouns",
        "question": "Which word correctly replaces 'the dog' in the sentence: 'The dog is friendly.'?",
        "options": ["He", "It", "She"],
        "correct_answer": "It",
        "explanation": "We use 'It' when referring to an animal whose gender is unspecified.",
        "difficulty": 1,
        "exercise_type": "multiple_choice",
    },
    # ── GRAMMAR – INTERMEDIATE ────────────────────────────────────────────
    {
        "id": "grammar_006",
        "level": "intermediate",
        "skill": "grammar",
        "topic": "present perfect",
        "question": "She ___ already eaten lunch.",
        "options": ["has", "have", "had"],
        "correct_answer": "has",
        "explanation": "With 'she', we use 'has' in the present perfect tense.",
        "difficulty": 2,
        "exercise_type": "fill_in_the_blank",
    },
    {
        "id": "grammar_007",
        "level": "intermediate",
        "skill": "grammar",
        "topic": "conditionals",
        "question": "If it ___ tomorrow, we will cancel the picnic.",
        "options": ["rains", "rain", "rained"],
        "correct_answer": "rains",
        "explanation": "In a first conditional sentence, the 'if' clause uses the simple present tense.",
        "difficulty": 2,
        "exercise_type": "fill_in_the_blank",
    },
    {
        "id": "grammar_008",
        "level": "intermediate",
        "skill": "grammar",
        "topic": "passive voice",
        "question": "Correct the sentence: 'The book written by the teacher was.'",
        "options": [
            "The book was written by the teacher.",
            "The teacher was written by the book.",
            "By the teacher, the book written was.",
        ],
        "correct_answer": "The book was written by the teacher.",
        "explanation": "In passive voice, the subject receives the action. The correct order is: subject + was/were + past participle + by + agent.",
        "difficulty": 2,
        "exercise_type": "sentence_correction",
    },
    {
        "id": "grammar_009",
        "level": "intermediate",
        "skill": "grammar",
        "topic": "relative clauses",
        "question": "The woman ___ lives next door is a doctor.",
        "options": ["who", "which", "whom"],
        "correct_answer": "who",
        "explanation": "'Who' is used for people as the subject of the relative clause.",
        "difficulty": 2,
        "exercise_type": "fill_in_the_blank",
    },
    # ── GRAMMAR – ADVANCED ────────────────────────────────────────────────
    {
        "id": "grammar_010",
        "level": "advanced",
        "skill": "grammar",
        "topic": "subjunctive mood",
        "question": "The committee recommended that she ___ the project immediately.",
        "options": ["begin", "begins", "began"],
        "correct_answer": "begin",
        "explanation": "After verbs like 'recommend' or 'suggest', the subjunctive uses the base form of the verb regardless of the subject.",
        "difficulty": 3,
        "exercise_type": "fill_in_the_blank",
    },
    {
        "id": "grammar_011",
        "level": "advanced",
        "skill": "grammar",
        "topic": "inversion",
        "question": "Correct the sentence: 'Never I have seen such a beautiful sunset.'",
        "options": [
            "Never have I seen such a beautiful sunset.",
            "Never I seen have such a beautiful sunset.",
            "Never such a beautiful sunset I have seen.",
        ],
        "correct_answer": "Never have I seen such a beautiful sunset.",
        "explanation": "When a negative adverb like 'never' starts a sentence, the subject and auxiliary verb are inverted.",
        "difficulty": 3,
        "exercise_type": "sentence_correction",
    },
    # ── VOCABULARY – BEGINNER ─────────────────────────────────────────────
    {
        "id": "vocab_001",
        "level": "beginner",
        "skill": "vocabulary",
        "topic": "colours and everyday words",
        "question": "What is the opposite of 'big'?",
        "options": ["tall", "small", "fast"],
        "correct_answer": "small",
        "explanation": "'Small' is the antonym of 'big'. Antonyms are words with opposite meanings.",
        "difficulty": 1,
        "exercise_type": "vocabulary",
    },
    {
        "id": "vocab_002",
        "level": "beginner",
        "skill": "vocabulary",
        "topic": "daily actions",
        "question": "Which word means 'to move through water using your arms and legs'?",
        "options": ["run", "swim", "jump"],
        "correct_answer": "swim",
        "explanation": "'Swim' means to move through water. 'Run' is on land, 'jump' is in the air.",
        "difficulty": 1,
        "exercise_type": "vocabulary",
    },
    {
        "id": "vocab_003",
        "level": "beginner",
        "skill": "vocabulary",
        "topic": "numbers and time",
        "question": "How many days are in a week?",
        "options": ["five", "seven", "ten"],
        "correct_answer": "seven",
        "explanation": "A week has seven days: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, and Sunday.",
        "difficulty": 1,
        "exercise_type": "vocabulary",
    },
    # ── VOCABULARY – INTERMEDIATE ─────────────────────────────────────────
    {
        "id": "vocab_004",
        "level": "intermediate",
        "skill": "vocabulary",
        "topic": "synonyms",
        "question": "Which word is a synonym for 'happy'?",
        "options": ["sad", "joyful", "angry"],
        "correct_answer": "joyful",
        "explanation": "'Joyful' means feeling great happiness, which is the same as 'happy'. Synonyms are words with similar meanings.",
        "difficulty": 2,
        "exercise_type": "vocabulary",
    },
    {
        "id": "vocab_005",
        "level": "intermediate",
        "skill": "vocabulary",
        "topic": "phrasal verbs",
        "question": "What does 'give up' mean?",
        "options": ["to start something new", "to stop trying", "to give a gift"],
        "correct_answer": "to stop trying",
        "explanation": "'Give up' is a phrasal verb meaning to stop trying to do something.",
        "difficulty": 2,
        "exercise_type": "vocabulary",
    },
    {
        "id": "vocab_006",
        "level": "intermediate",
        "skill": "vocabulary",
        "topic": "word forms",
        "question": "The noun form of 'educate' is ___.",
        "options": ["educational", "education", "educator"],
        "correct_answer": "education",
        "explanation": "'Education' is the noun form. 'Educational' is an adjective and 'educator' is a person noun.",
        "difficulty": 2,
        "exercise_type": "vocabulary",
    },
    # ── VOCABULARY – ADVANCED ─────────────────────────────────────────────
    {
        "id": "vocab_007",
        "level": "advanced",
        "skill": "vocabulary",
        "topic": "formal vocabulary",
        "question": "The word 'ameliorate' most closely means ___.",
        "options": ["to make worse", "to improve", "to ignore"],
        "correct_answer": "to improve",
        "explanation": "'Ameliorate' is a formal word meaning to make something better or improve it.",
        "difficulty": 3,
        "exercise_type": "vocabulary",
    },
    {
        "id": "vocab_008",
        "level": "advanced",
        "skill": "vocabulary",
        "topic": "idioms",
        "question": "What does 'bite the bullet' mean?",
        "options": [
            "to eat something hard",
            "to endure a painful situation bravely",
            "to shoot a gun",
        ],
        "correct_answer": "to endure a painful situation bravely",
        "explanation": "'Bite the bullet' is an idiom meaning to endure a painful or difficult situation with courage.",
        "difficulty": 3,
        "exercise_type": "vocabulary",
    },
    # ── SENTENCE FORMATION – BEGINNER ────────────────────────────────────
    {
        "id": "sent_001",
        "level": "beginner",
        "skill": "sentence_formation",
        "topic": "word order",
        "question": "Arrange the words to make a correct sentence: 'school / to / I / go / every day'",
        "options": [
            "I go to school every day.",
            "Every day I school go to.",
            "School I go to every day.",
        ],
        "correct_answer": "I go to school every day.",
        "explanation": "The correct order is: Subject (I) + Verb (go) + Preposition (to) + Object (school) + Time (every day).",
        "difficulty": 1,
        "exercise_type": "sentence_correction",
    },
    {
        "id": "sent_002",
        "level": "beginner",
        "skill": "sentence_formation",
        "topic": "question formation",
        "question": "Which is the correct question form? (Statement: 'She likes mangoes.')",
        "options": [
            "Does she likes mangoes?",
            "Does she like mangoes?",
            "She does like mangoes?",
        ],
        "correct_answer": "Does she like mangoes?",
        "explanation": "In a yes/no question with 'does', the main verb returns to its base form. So 'likes' becomes 'like'.",
        "difficulty": 1,
        "exercise_type": "sentence_correction",
    },
    # ── SENTENCE FORMATION – INTERMEDIATE ────────────────────────────────
    {
        "id": "sent_003",
        "level": "intermediate",
        "skill": "sentence_formation",
        "topic": "combining sentences",
        "question": "Combine these two sentences into one: 'I was tired. I finished the work.'",
        "options": [
            "Although I was tired, I finished the work.",
            "I was tired but I finished because the work.",
            "I finished the work and tired I was.",
        ],
        "correct_answer": "Although I was tired, I finished the work.",
        "explanation": "'Although' introduces a contrast clause. It connects two ideas where the second happens despite the first.",
        "difficulty": 2,
        "exercise_type": "sentence_correction",
    },
    {
        "id": "sent_004",
        "level": "intermediate",
        "skill": "sentence_formation",
        "topic": "reported speech",
        "question": "Change to reported speech: He said, 'I am learning English.'",
        "options": [
            "He said that he is learning English.",
            "He said that he was learning English.",
            "He said that I am learning English.",
        ],
        "correct_answer": "He said that he was learning English.",
        "explanation": "In reported speech, the present continuous 'am learning' shifts to past continuous 'was learning'.",
        "difficulty": 2,
        "exercise_type": "sentence_correction",
    },
    # ── SENTENCE FORMATION – ADVANCED ────────────────────────────────────
    {
        "id": "sent_005",
        "level": "advanced",
        "skill": "sentence_formation",
        "topic": "complex sentences",
        "question": "Identify the correctly punctuated complex sentence.",
        "options": [
            "Despite the rain, the match continued and, the crowd cheered.",
            "Despite the rain the match continued, and the crowd cheered.",
            "Despite the rain, the match continued, and the crowd cheered.",
        ],
        "correct_answer": "Despite the rain, the match continued, and the crowd cheered.",
        "explanation": "A comma follows the introductory phrase 'Despite the rain,' and a comma comes before the coordinating conjunction 'and' in a compound structure.",
        "difficulty": 3,
        "exercise_type": "sentence_correction",
    },
    # ── SPEAKING – BEGINNER ───────────────────────────────────────────────
    {
        "id": "speak_001",
        "level": "beginner",
        "skill": "speaking",
        "topic": "self introduction",
        "question": "Tell me your name and one thing you like to do. Speak in a full sentence.",
        "options": None,
        "correct_answer": "my name is",
        "explanation": "A good answer includes 'My name is [name]' and a hobby or activity. For example: 'My name is Priya. I like reading books.'",
        "difficulty": 1,
        "exercise_type": "speaking_prompt",
    },
    {
        "id": "speak_002",
        "level": "beginner",
        "skill": "speaking",
        "topic": "describing objects",
        "question": "Describe what you see around you right now in one or two sentences.",
        "options": None,
        "correct_answer": "i see",
        "explanation": "A good answer starts with 'I see...' or 'There is...' and describes at least one object with a colour or shape.",
        "difficulty": 1,
        "exercise_type": "speaking_prompt",
    },
    # ── SPEAKING – INTERMEDIATE ───────────────────────────────────────────
    {
        "id": "speak_003",
        "level": "intermediate",
        "skill": "speaking",
        "topic": "expressing opinions",
        "question": "Do you prefer living in a city or in the countryside? Give one reason.",
        "options": None,
        "correct_answer": "because",
        "explanation": "A good answer states a preference and gives a reason using 'because'. For example: 'I prefer the city because there are more opportunities.'",
        "difficulty": 2,
        "exercise_type": "speaking_prompt",
    },
    {
        "id": "speak_004",
        "level": "intermediate",
        "skill": "speaking",
        "topic": "storytelling",
        "question": "Tell me about a time you helped someone. Use the past tense.",
        "options": None,
        "correct_answer": "helped",
        "explanation": "A good answer uses past-tense verbs like 'helped', 'gave', 'was'. For example: 'I helped my friend carry her books when she was sick.'",
        "difficulty": 2,
        "exercise_type": "speaking_prompt",
    },
    # ── SPEAKING – ADVANCED ───────────────────────────────────────────────
    {
        "id": "speak_005",
        "level": "advanced",
        "skill": "speaking",
        "topic": "argumentation",
        "question": "Should technology be used more in classrooms? Give two points to support your view.",
        "options": None,
        "correct_answer": "technology",
        "explanation": "A strong answer takes a position and supports it with two distinct points, using linking words like 'firstly', 'furthermore', 'however'.",
        "difficulty": 3,
        "exercise_type": "speaking_prompt",
    },
    # ── COMPREHENSION – BEGINNER ──────────────────────────────────────────
    {
        "id": "comp_001",
        "level": "beginner",
        "skill": "comprehension",
        "topic": "reading simple text",
        "question": "Read this: 'Tom has a red ball. He plays with it every evening.' — What colour is Tom's ball?",
        "options": ["blue", "red", "green"],
        "correct_answer": "red",
        "explanation": "The text says 'Tom has a red ball.' The answer is directly stated.",
        "difficulty": 1,
        "exercise_type": "multiple_choice",
    },
    {
        "id": "comp_002",
        "level": "beginner",
        "skill": "comprehension",
        "topic": "understanding instructions",
        "question": "If someone says 'Turn left at the corner', which direction do you turn?",
        "options": ["right", "left", "straight"],
        "correct_answer": "left",
        "explanation": "The instruction clearly says 'turn left'. Listening carefully to directions is an important communication skill.",
        "difficulty": 1,
        "exercise_type": "multiple_choice",
    },
    # ── COMPREHENSION – INTERMEDIATE ──────────────────────────────────────
    {
        "id": "comp_003",
        "level": "intermediate",
        "skill": "comprehension",
        "topic": "inference",
        "question": "Read: 'Riya did not bring an umbrella. Her shoes got wet on the way home.' — What was the weather like?",
        "options": ["sunny", "rainy", "snowy"],
        "correct_answer": "rainy",
        "explanation": "The text doesn't mention rain directly, but wet shoes after forgetting an umbrella implies it was raining.",
        "difficulty": 2,
        "exercise_type": "multiple_choice",
    },
    {
        "id": "comp_004",
        "level": "intermediate",
        "skill": "comprehension",
        "topic": "main idea",
        "question": "Read: 'Exercising regularly helps keep your heart healthy, strengthens your muscles, and improves your mood.' — What is the main idea?",
        "options": [
            "Exercise makes you feel sad.",
            "Regular exercise has many health benefits.",
            "You should go to the gym every day.",
        ],
        "correct_answer": "Regular exercise has many health benefits.",
        "explanation": "The sentence lists three benefits of exercise. The main idea is that regular exercise is good for health.",
        "difficulty": 2,
        "exercise_type": "multiple_choice",
    },
    # ── COMPREHENSION – ADVANCED ──────────────────────────────────────────
    {
        "id": "comp_005",
        "level": "advanced",
        "skill": "comprehension",
        "topic": "author's tone",
        "question": "Read: 'Once again, the government promised reforms. Once again, nothing changed.' — What is the author's tone?",
        "options": ["optimistic", "sarcastic", "neutral"],
        "correct_answer": "sarcastic",
        "explanation": "The repeated 'Once again' and the contrast between promise and inaction show sarcasm — a tone that implies criticism through irony.",
        "difficulty": 3,
        "exercise_type": "multiple_choice",
    },
]

# Build a lookup index by exercise id for O(1) retrieval
_EXERCISE_INDEX: dict[str, dict[str, Any]] = {ex["id"]: ex for ex in EXERCISES}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_next_exercise(
    level: str,
    skill: str,
    topic: str | None = None,
    difficulty: int | None = None,
    exclude_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return a suitable exercise from the local dataset.

    Args:
        level:       Learner level — "beginner", "intermediate", or "advanced".
        skill:       Skill area — "grammar", "vocabulary", "sentence_formation",
                     "speaking", or "comprehension".
        topic:       Optional topic filter (partial match, case-insensitive).
        difficulty:  Optional difficulty filter (1=easy, 2=medium, 3=hard).
        exclude_ids: Exercise IDs to skip (used to avoid repeating recent exercises).

    Returns:
        A result dict with keys: success, exercise, source, data_version.
        On failure: success=False and an error message.
    """
    try:
        exclude_ids = exclude_ids or []
        level = level.lower().strip()
        skill = skill.lower().strip().replace(" ", "_")

        candidates = [
            ex
            for ex in EXERCISES
            if ex["level"] == level
            and ex["skill"] == skill
            and ex["id"] not in exclude_ids
        ]

        if not candidates:
            # Relax: ignore exclude_ids if nothing left
            candidates = [
                ex for ex in EXERCISES if ex["level"] == level and ex["skill"] == skill
            ]

        if not candidates:
            # Relax: try any exercise at this level
            candidates = [ex for ex in EXERCISES if ex["level"] == level]

        if not candidates:
            # Last resort: any exercise
            candidates = list(EXERCISES)

        # Optional topic filter (partial, case-insensitive)
        if topic:
            topic_lower = topic.lower()
            topic_matches = [
                ex for ex in candidates if topic_lower in ex["topic"].lower()
            ]
            if topic_matches:
                candidates = topic_matches

        # Optional difficulty filter
        if difficulty is not None:
            diff_matches = [ex for ex in candidates if ex["difficulty"] == difficulty]
            if diff_matches:
                candidates = diff_matches

        chosen = random.choice(candidates)

        # Return a clean copy — do not expose internal fields the LLM shouldn't see
        exercise_payload = {
            "id": chosen["id"],
            "question": chosen["question"],
            "options": chosen.get("options"),
            "level": chosen["level"],
            "skill": chosen["skill"],
            "topic": chosen["topic"],
            "difficulty": chosen["difficulty"],
            "exercise_type": chosen["exercise_type"],
        }

        logger.info(
            "get_next_exercise: returned id=%s level=%s skill=%s",
            chosen["id"],
            chosen["level"],
            chosen["skill"],
        )

        return {
            "success": True,
            "exercise": exercise_payload,
            "source": DATASET_SOURCE,
            "data_version": DATA_VERSION,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("get_next_exercise failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": "Could not retrieve an exercise from the dataset.",
            "source": DATASET_SOURCE,
            "data_version": DATA_VERSION,
        }


def evaluate_answer(exercise_id: str, learner_answer: str) -> dict[str, Any]:
    """Evaluate a learner's answer against the stored exercise.

    Uses flexible matching for open-ended / speaking exercises.
    Always returns supportive feedback phrasing.

    Args:
        exercise_id:    The id of the exercise being answered.
        learner_answer: The learner's spoken or typed response.

    Returns:
        A result dict with keys: success, correct, score, feedback,
        correct_answer, explanation, exercise_id.
        On failure: success=False and an error message.
    """
    try:
        if not exercise_id or not isinstance(exercise_id, str):
            raise ValueError("Invalid exercise_id provided.")

        exercise = _EXERCISE_INDEX.get(exercise_id.strip())
        if exercise is None:
            raise KeyError(f"Exercise '{exercise_id}' not found in dataset.")

        if not learner_answer or not isinstance(learner_answer, str):
            raise ValueError("Learner answer is empty or invalid.")

        correct_answer: str = str(exercise["correct_answer"])
        exercise_type: str = exercise["exercise_type"]
        explanation: str = exercise["explanation"]

        is_correct = _check_answer(exercise_type, correct_answer, learner_answer)
        score = 1 if is_correct else 0

        if is_correct:
            feedback = _positive_feedback()
        else:
            feedback = _supportive_feedback(correct_answer)

        logger.info(
            "evaluate_answer: exercise_id=%s correct=%s learner_answer=%r",
            exercise_id,
            is_correct,
            learner_answer,
        )

        return {
            "success": True,
            "correct": is_correct,
            "score": score,
            "feedback": feedback,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "exercise_id": exercise_id,
        }

    except KeyError as exc:
        logger.error("evaluate_answer — exercise not found: %s", exc)
        return {
            "success": False,
            "error": f"Exercise not found: {exc}",
            "exercise_id": exercise_id,
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("evaluate_answer failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": "Could not evaluate the answer right now.",
            "exercise_id": exercise_id,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalise(text: str) -> str:
    """Lower-case, strip punctuation and extra whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def _check_answer(exercise_type: str, correct_answer: str, learner_answer: str) -> bool:
    """Return True if the learner's answer is considered correct.

    Speaking prompts use keyword-presence matching; all others use normalised
    exact matching (so 'Goes', 'goes.', ' GOES ' all match 'goes').
    """
    norm_correct = _normalise(correct_answer)
    norm_learner = _normalise(learner_answer)

    if exercise_type == "speaking_prompt":
        # Accept if the learner's answer contains the key word/phrase
        return norm_correct in norm_learner

    # For fill_in_the_blank, multiple_choice, vocabulary, sentence_correction:
    # Accept if normalised strings match, OR if the correct answer is contained
    # in the learner's answer (handles "The answer is goes" → "goes").
    if norm_correct == norm_learner:
        return True
    if norm_correct in norm_learner:
        return True
    return False


# Positive feedback — rotate through several supportive phrases
_POSITIVE_PHRASES = [
    "Excellent! You got it right.",
    "Well done! That's correct.",
    "Fantastic! That's exactly right.",
    "Great job! You're doing brilliantly.",
    "Spot on! That's the correct answer.",
]

# Supportive wrong-answer feedback — never shaming, always encouraging
_SUPPORTIVE_PHRASES = [
    "Good attempt! The correct answer is '{answer}'.",
    "Almost there! The right answer is '{answer}'.",
    "Nice try! The correct form is '{answer}'.",
    "You're getting there! The answer we were looking for is '{answer}'.",
    "Great effort! Let's look at this together — the correct answer is '{answer}'.",
]


def _positive_feedback() -> str:
    return random.choice(_POSITIVE_PHRASES)


def _supportive_feedback(correct_answer: str) -> str:
    template = random.choice(_SUPPORTIVE_PHRASES)
    return template.format(answer=correct_answer)
