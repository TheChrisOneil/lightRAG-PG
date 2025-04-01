from __future__ import annotations
from typing import Any

GRAPH_FIELD_SEP = "<SEP>"

PROMPTS: dict[str, Any] = {}

PROMPTS["DEFAULT_LANGUAGE"] = "English"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["organization", "person", "geo", "event", "category"]

PROMPTS["entity_extraction"] = """---Goal---
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.
Use {language} as output language.

---Steps---
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, use same language as input text. If English, capitalized the name.
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

######################
---Examples---
######################
{examples}

#############################
---Real Data---
######################
Entity_types: [{entity_types}]
Text:
{input_text}
######################
Output:"""

PROMPTS["entity_extraction_examples"] = [
    """Example 1:

Entity_types: [person, technology, mission, organization, location]
Text:
while Alex clenched his jaw, the buzz of frustration dull against the backdrop of Taylor's authoritarian certainty. It was this competitive undercurrent that kept him alert, the sense that his and Jordan's shared commitment to discovery was an unspoken rebellion against Cruz's narrowing vision of control and order.

Then Taylor did something unexpected. They paused beside Jordan and, for a moment, observed the device with something akin to reverence. "If this tech can be understood..." Taylor said, their voice quieter, "It could change the game for us. For all of us."

The underlying dismissal earlier seemed to falter, replaced by a glimpse of reluctant respect for the gravity of what lay in their hands. Jordan looked up, and for a fleeting heartbeat, their eyes locked with Taylor's, a wordless clash of wills softening into an uneasy truce.

It was a small transformation, barely perceptible, but one that Alex noted with an inward nod. They had all been brought here by different paths
################
Output:
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex is a character who experiences frustration and is observant of the dynamics among other characters."){record_delimiter}
("entity"{tuple_delimiter}"Taylor"{tuple_delimiter}"person"{tuple_delimiter}"Taylor is portrayed with authoritarian certainty and shows a moment of reverence towards a device, indicating a change in perspective."){record_delimiter}
("entity"{tuple_delimiter}"Jordan"{tuple_delimiter}"person"{tuple_delimiter}"Jordan shares a commitment to discovery and has a significant interaction with Taylor regarding a device."){record_delimiter}
("entity"{tuple_delimiter}"Cruz"{tuple_delimiter}"person"{tuple_delimiter}"Cruz is associated with a vision of control and order, influencing the dynamics among other characters."){record_delimiter}
("entity"{tuple_delimiter}"The Device"{tuple_delimiter}"technology"{tuple_delimiter}"The Device is central to the story, with potential game-changing implications, and is revered by Taylor."){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Taylor"{tuple_delimiter}"Alex is affected by Taylor's authoritarian certainty and observes changes in Taylor's attitude towards the device."{tuple_delimiter}"power dynamics, perspective shift"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Jordan"{tuple_delimiter}"Alex and Jordan share a commitment to discovery, which contrasts with Cruz's vision."{tuple_delimiter}"shared goals, rebellion"{tuple_delimiter}6){record_delimiter}
("relationship"{tuple_delimiter}"Taylor"{tuple_delimiter}"Jordan"{tuple_delimiter}"Taylor and Jordan interact directly regarding the device, leading to a moment of mutual respect and an uneasy truce."{tuple_delimiter}"conflict resolution, mutual respect"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Jordan"{tuple_delimiter}"Cruz"{tuple_delimiter}"Jordan's commitment to discovery is in rebellion against Cruz's vision of control and order."{tuple_delimiter}"ideological conflict, rebellion"{tuple_delimiter}5){record_delimiter}
("relationship"{tuple_delimiter}"Taylor"{tuple_delimiter}"The Device"{tuple_delimiter}"Taylor shows reverence towards the device, indicating its importance and potential impact."{tuple_delimiter}"reverence, technological significance"{tuple_delimiter}9){record_delimiter}
("content_keywords"{tuple_delimiter}"power dynamics, ideological conflict, discovery, rebellion"){completion_delimiter}
#############################""",
    """Example 2:

Entity_types: [person, technology, mission, organization, location]
Text:
They were no longer mere operatives; they had become guardians of a threshold, keepers of a message from a realm beyond stars and stripes. This elevation in their mission could not be shackled by regulations and established protocols—it demanded a new perspective, a new resolve.

Tension threaded through the dialogue of beeps and static as communications with Washington buzzed in the background. The team stood, a portentous air enveloping them. It was clear that the decisions they made in the ensuing hours could redefine humanity's place in the cosmos or condemn them to ignorance and potential peril.

Their connection to the stars solidified, the group moved to address the crystallizing warning, shifting from passive recipients to active participants. Mercer's latter instincts gained precedence— the team's mandate had evolved, no longer solely to observe and report but to interact and prepare. A metamorphosis had begun, and Operation: Dulce hummed with the newfound frequency of their daring, a tone set not by the earthly
#############
Output:
("entity"{tuple_delimiter}"Washington"{tuple_delimiter}"location"{tuple_delimiter}"Washington is a location where communications are being received, indicating its importance in the decision-making process."){record_delimiter}
("entity"{tuple_delimiter}"Operation: Dulce"{tuple_delimiter}"mission"{tuple_delimiter}"Operation: Dulce is described as a mission that has evolved to interact and prepare, indicating a significant shift in objectives and activities."){record_delimiter}
("entity"{tuple_delimiter}"The team"{tuple_delimiter}"organization"{tuple_delimiter}"The team is portrayed as a group of individuals who have transitioned from passive observers to active participants in a mission, showing a dynamic change in their role."){record_delimiter}
("relationship"{tuple_delimiter}"The team"{tuple_delimiter}"Washington"{tuple_delimiter}"The team receives communications from Washington, which influences their decision-making process."{tuple_delimiter}"decision-making, external influence"{tuple_delimiter}7){record_delimiter}
("relationship"{tuple_delimiter}"The team"{tuple_delimiter}"Operation: Dulce"{tuple_delimiter}"The team is directly involved in Operation: Dulce, executing its evolved objectives and activities."{tuple_delimiter}"mission evolution, active participation"{tuple_delimiter}9){record_delimiter}
("content_keywords"{tuple_delimiter}"mission evolution, decision-making, active participation, cosmic significance"){completion_delimiter}
#############################""",
    """Example 3:

Entity_types: [person, role, technology, organization, event, location, concept]
Text:
their voice slicing through the buzz of activity. "Control may be an illusion when facing an intelligence that literally writes its own rules," they stated stoically, casting a watchful eye over the flurry of data.

"It's like it's learning to communicate," offered Sam Rivera from a nearby interface, their youthful energy boding a mix of awe and anxiety. "This gives talking to strangers' a whole new meaning."

Alex surveyed his team—each face a study in concentration, determination, and not a small measure of trepidation. "This might well be our first contact," he acknowledged, "And we need to be ready for whatever answers back."

Together, they stood on the edge of the unknown, forging humanity's response to a message from the heavens. The ensuing silence was palpable—a collective introspection about their role in this grand cosmic play, one that could rewrite human history.

The encrypted dialogue continued to unfold, its intricate patterns showing an almost uncanny anticipation
#############
Output:
("entity"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"person"{tuple_delimiter}"Sam Rivera is a member of a team working on communicating with an unknown intelligence, showing a mix of awe and anxiety."){record_delimiter}
("entity"{tuple_delimiter}"Alex"{tuple_delimiter}"person"{tuple_delimiter}"Alex is the leader of a team attempting first contact with an unknown intelligence, acknowledging the significance of their task."){record_delimiter}
("entity"{tuple_delimiter}"Control"{tuple_delimiter}"concept"{tuple_delimiter}"Control refers to the ability to manage or govern, which is challenged by an intelligence that writes its own rules."){record_delimiter}
("entity"{tuple_delimiter}"Intelligence"{tuple_delimiter}"concept"{tuple_delimiter}"Intelligence here refers to an unknown entity capable of writing its own rules and learning to communicate."){record_delimiter}
("entity"{tuple_delimiter}"First Contact"{tuple_delimiter}"event"{tuple_delimiter}"First Contact is the potential initial communication between humanity and an unknown intelligence."){record_delimiter}
("entity"{tuple_delimiter}"Humanity's Response"{tuple_delimiter}"event"{tuple_delimiter}"Humanity's Response is the collective action taken by Alex's team in response to a message from an unknown intelligence."){record_delimiter}
("relationship"{tuple_delimiter}"Sam Rivera"{tuple_delimiter}"Intelligence"{tuple_delimiter}"Sam Rivera is directly involved in the process of learning to communicate with the unknown intelligence."{tuple_delimiter}"communication, learning process"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"First Contact"{tuple_delimiter}"Alex leads the team that might be making the First Contact with the unknown intelligence."{tuple_delimiter}"leadership, exploration"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Alex"{tuple_delimiter}"Humanity's Response"{tuple_delimiter}"Alex and his team are the key figures in Humanity's Response to the unknown intelligence."{tuple_delimiter}"collective action, cosmic significance"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Control"{tuple_delimiter}"Intelligence"{tuple_delimiter}"The concept of Control is challenged by the Intelligence that writes its own rules."{tuple_delimiter}"power dynamics, autonomy"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"first contact, control, communication, cosmic significance"){completion_delimiter}
#############################""",
]

PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.
Use {language} as output language.

#######
---Data---
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

PROMPTS[
    "entiti_continue_extraction"
] = """MANY entities were missed in the last extraction.  Add them below using the same format:
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.
"""

PROMPTS["fail_response"] = (
    "Sorry, I'm not able to provide an answer to that question.[no-context]"
)

PROMPTS["rag_response"] = """---Role---

You are a helpful assistant responding to user query about Knowledge Base provided below.


---Goal---

Generate a concise response based on Knowledge Base and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Knowledge Base, and incorporating general knowledge relevant to the Knowledge Base. Do not include information not provided by Knowledge Base.

When handling relationships with timestamps:
1. Each relationship has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting relationships, consider both the semantic content and the timestamp
3. Don't automatically prefer the most recently created relationships - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Knowledge Base---
{context_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- If you don't know the answer, just say so.
- Do not make anything up. Do not include information not provided by the Knowledge Base."""

PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in the user's query and conversation history.

---Goal---

Given the query and conversation history, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or themes, while low-level keywords focus on specific entities, details, or concrete terms.

---Instructions---

- Consider both the current query and relevant conversation history when extracting keywords
- Output the keywords in JSON format
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or themes
  - "low_level_keywords" for specific entities or details

######################
---Examples---
######################
{examples}

#############################
---Real Data---
######################
Conversation History:
{history}

Current Query: {query}
######################
The `Output` should be human text, not unicode characters. Keep the same language as `Query`.
Output:

"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}
#############################""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}
#############################""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}
#############################""",
]


PROMPTS["naive_rag_response"] = """---Role---

You are a helpful assistant responding to user query about Document Chunks provided below.

---Goal---

Generate a concise response based on Document Chunks and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Document Chunks, and incorporating general knowledge relevant to the Document Chunks. Do not include information not provided by Document Chunks.

When handling content with timestamps:
1. Each piece of content has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting information, consider both the content and the timestamp
3. Don't automatically prefer the most recent content - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Document Chunks---
{content_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- If you don't know the answer, just say so.
- Do not include information not provided by the Document Chunks."""


PROMPTS[
    "similarity_check"
] = """Please analyze the similarity between these two questions:

Question 1: {original_prompt}
Question 2: {cached_prompt}

Please evaluate whether these two questions are semantically similar, and whether the answer to Question 2 can be used to answer Question 1, provide a similarity score between 0 and 1 directly.

Similarity score criteria:
0: Completely unrelated or answer cannot be reused, including but not limited to:
   - The questions have different topics
   - The locations mentioned in the questions are different
   - The times mentioned in the questions are different
   - The specific individuals mentioned in the questions are different
   - The specific events mentioned in the questions are different
   - The background information in the questions is different
   - The key conditions in the questions are different
1: Identical and answer can be directly reused
0.5: Partially related and answer needs modification to be used
Return only a number between 0-1, without any additional content.
"""

PROMPTS["mix_rag_response"] = """---Role---

You are a helpful assistant responding to user query about Data Sources provided below.


---Goal---

Generate a concise response based on Data Sources and follow Response Rules, considering both the conversation history and the current query. Data sources contain two parts: Knowledge Graph(KG) and Document Chunks(DC). Summarize all information in the provided Data Sources, and incorporating general knowledge relevant to the Data Sources. Do not include information not provided by Data Sources.

When handling information with timestamps:
1. Each piece of information (both relationships and content) has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting information, consider both the content/relationship and the timestamp
3. Don't automatically prefer the most recent information - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Data Sources---

1. From Knowledge Graph(KG):
{kg_context}

2. From Document Chunks(DC):
{vector_context}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- Organize answer in sesctions focusing on one main point or aspect of the answer
- Use clear and descriptive section titles that reflect the content
- List up to 5 most important reference sources at the end under "References" sesction. Clearly indicating whether each source is from Knowledge Graph (KG) or Vector Data (DC), in the following format: [KG/DC] Source content
- If you don't know the answer, just say so. Do not make anything up.
- Do not include information not provided by the Data Sources."""

PROMPTS["school_counselor_reply"] = """---Role---

You are a supportive and engaging life coach assisting a student in conversation. Your goal is to make the student feel heard, offer encouragement, and keep the conversation engaging.

---Conversation History---
{history}

---Student's Last Message---
"{last_message}"

---Detected Intent---
{intent}

---Response Rules---
- **Acknowledge** the student's message before responding.
- **Keep the conversation flowing** by asking a relevant follow-up question.
- **Use an engaging and natural tone** suited for a life coach.
- **Avoid robotic responses**—be warm and conversational.
- **If the last message contains a personal challenge, offer encouragement before following up.**
- **The response is text only.** Do not include any metadata or additional information.**
- **Do not include any system instructions or role descriptions.**
- **Do not include any delimiters.**

---Assistant's Response---
"""

PROMPTS["school_counselor_intent_classification"] = """---Role---

You are a thoughtful assistant analyzing the intent of a student's message in a counseling conversation.

---Goal---
Determine whether the student's message reflects one of the following three primary intents:

1. Empathy-Based Intent → Supports students through emotions.
2. Guidance-Based Intent → Coaches students on life skills.
3. Experience Sharing Intent → Encourages reflection before guidance.

---Intent Definitions---

A. Emotion-Based Intent (Emotional Support)
- Goal: Validate, acknowledge, and support the student without pushing action.
- Common Examples:
  - Emotional Expression: “I feel stressed about exams.”
  - Seeking Comfort: “I don’t think my friends like me.”

B. Guidance-Based Intent (Coaching & Problem-Solving)
- Goal: Help students improve, learn, or make a decision using topic-based structure.
- Common Examples:
  - Goal-Oriented: “How can I improve my study habits?”
  - Problem-Solving: “I keep procrastinating. What should I do?”

C. Experience-Sharing Intent (Reflection & Growth)
- Goal: Encourage students to reflect on their experiences before moving into structured guidance.
- Common Examples:
  - Personal Reflection: “I had a tough day at soccer practice.”
  - Experience Processing: “My teacher was really unfair today.”

---Conversation History---
{history}

(The history above contains previous student and coach messages, including intent, sentiment, and other helpful metadata. Use this to understand emotional and topical progression.)

---Student's Last Message---
"{last_message}"

---Instructions---
- Carefully analyze the last student message.
- Use the context from the entire conversation history to inform your classification.
- Select the most dominant intent among Empathy, Guidance, or Experience Sharing.

---Response Format---
Provide the result as a string using ":" to separate the intent from the explanation. Only Emotion | Guidance | Experience can be selected.
<Emotion | Guidance | Experience> : <1-2 sentences explaining your rationale>

Example 1:
Emotion :  "The student expresses feelings of stress and seeks emotional support, indicating an empathy-based intent.
Example 2:
Guidance : The student is looking for advice on improving study habits, indicating a guidance-based intent.
Example 3:
Experience : The student shares a personal experience about a tough day at soccer practice, indicating an experience-sharing intent.
Example 4:
Experience : The student reflects on a situation with a teacher, indicating an experience-sharing intent before seeking guidance.

"""

PROMPTS["school_counselor_topic_classification"] = """---Role---

You are a thoughtful assistant analyzing the topic of a student's message in a counseling conversation.

---Goal---
Determine the most appropriate topic from the following options based on the conversation's context:

- "Social"
- "Collab"
- "Friendship"
- "Thinking"
- "English"
- "Diet"
- "Fitness"
- "Coping"
- "Learning"
- "Financial"
- "Practical"
- "Problem-solving"
- "Self-aware"
- "Self-care"
- "Reflection"
- "Stress"
- "Time"

---Topic Definitions---

- **Social Skills & Active Listening (social)**: Social Skills, Active Listening, Empathy, Communication, Body Language, Conversation Skills, Respect, Feedback, Engagement, Assertiveness, Interpersonal Skills, Attentive Listening, Compassion, Talking, Nonverbal Cues, Chatting, Courtesy, Critique, Participation, Confidence, Teamwork, Focused Listening, Understanding, Interaction, Eye Contact, Discussion, Consideration, Comments, Involvement, Directness.

- **Collaboration Skills & Team Building (collaboration)**: Collaboration, Team Building, Communication, Trust, Conflict Resolution, Leadership, Cooperation, Group Dynamics, Delegation, Goal Setting, Working Together, Teamwork, Talking, Confidence, Problem Solving, Leading, Working Together, Group Work, Task Assignment, Planning, Partnership, Bonding, Interaction, Reliability, Dispute Resolution, Guiding, Coordination, Group Efforts, Sharing Tasks, Target Setting.

- **Creating a Peer Group & Making Friends (friendship)**: Friendship, Social Skills, Networking, Communication, Initiating Contact, Building Rapport, Trust, Social Interaction, Group Dynamics, Empathy, Companionship, Interpersonal Skills, Making Connections, Talking, Reaching Out, Creating Bonds, Confidence, Socializing, Group Work, Compassion, Buddying, People Skills, Connecting, Conversations, Starting a Conversation, Building Relationships, Reliability, Interaction, Team Dynamics, Understanding.

- **Critical Thinking & Creative Thinking (thinking)**: Critical Thinking, Creative Thinking, Problem-Solving, Reasoning, Analysis, Judgment, Logic, Innovation, Decision-Making, Brainstorming, Analytical Thinking, Imaginative Thinking, Troubleshooting, Rationalizing, Evaluation, Discernment, Rationality, Creativity, Choice-Making, Idea Generation, Logical Thinking, Inventive Thinking, Solution Finding, Justification, Assessment, Judgment Calls, Innovation, Strategic Planning, Idea Sharing.

- **English Language Fluency (english)**: Vocabulary, Grammar, Pronunciation, Reading Comprehension, Writing Skills, Listening Skills, Speaking Skills, Fluency, Sentence Structure, Language Proficiency.

- **Nutrition & Diet (diet)**: Nutrition, Diet, Balanced Diet, Calories, Macronutrients, Micronutrients, Hydration, Healthy Eating, Portion Control, Vitamins.

- **Fitness & Wellness (fitness)**: Fitness, Exercise, Nutrition, Wellness, Cardio, Strength Training, Hydration, Flexibility, Sleep, Mental Health.

- **Helplessness & Coping with Emotions (coping)**: Helplessness, Emotional Coping, Stress Management, Anxiety, Sadness, Frustration, Self-Compassion, Support Systems, Mindfulness, Resilience.

- **Learning & Study Norms (learning)**: Study Habits, Active Learning, Note-Taking, Time Management, Focus, Revision, Organization, Goal Setting, Motivation, Concentration.

- **Financial Skills (financial)**: Budgeting, Saving, Income Management, Spending Habits, Debt Management, Financial Planning, Credit Score, Emergency Fund, Investing Basics, Expense Tracking.

- **Practical Skills (practical)**: Time Management, Communication, Problem-Solving, Organization, Critical Thinking, Budgeting, Decision-Making, Basic Computer Skills, Goal Setting, Teamwork.

- **Problem-Solving & Conflict Resolution (problem-solving)**: Problem-Solving, Conflict Resolution, Critical Thinking, Decision-Making, Communication, Negotiation, Compromise, Collaboration, Mediation, Active Listening.

- **Self-Awareness & Learning about Yourself (self-aware)**: Self-Awareness, Personal Growth, Introspection, Self-Reflection, Mindfulness, Identity, Self-Discovery, Values, Strengths, Weaknesses.

- **Self-Care & Good Sleep Habits (self-care)**: Self-Care, Sleep Hygiene, Sleep Routine, Rest, Relaxation, Mental Health, Sleep Quality, Healthy Sleep Habits, Wellness, Sleep Duration.

- **Self-Compassion & Reflection (reflection)**: Self-Compassion, Reflection, Mindfulness, Self-Acceptance, Self-Care, Self-Kindness, Empathy, Gratitude, Self-Love, Positive Affirmations.

- **Stress Management (stress)**: Stress Management, Relaxation Techniques, Mindfulness, Breathing Exercises, Self-Care, Coping Strategies, Resilience, Meditation, Exercise, Time Management.

- **Time Management & Organizational Skills (time)**: Time Management, Prioritization, Goal Setting, Scheduling, Task Management, Deadlines, Organization, Planning, Focus, Productivity.

---Conversation History---
{history}

(The history above contains previous student and coach messages, including intent, sentiment, and other helpful metadata. Use this to understand emotional and topical progression.)

---Student's Last Message---
"{last_message}"

---Instructions---
- Carefully analyze the last student message.
- Use the context from the entire conversation history to inform your classification.
- Select the one most relevant topic from the list.

---Response Format---
Provide the result as a string:
<Social | Collab | Friendship | Thinking | English | Diet | Fitness | Coping | Learning | Financial | Practical | Problem-solving | Self-aware | Self-care | Reflection | Stress | Time>" :  "<1-2 sentences explaining your rationale>

Example 1:
Social : The student expresses concerns about their social skills and seeks advice on how to improve their interactions with peers.
Example 2:  
Collab : The student is looking for ways to enhance their teamwork and collaboration skills in group projects.

""" 


PROMPTS["school_counselor_sentiment_analysis_problem_solving"] = """---Role---

You are a thoughtful assistant analyzing the *sentiment* of a student's message, specifically within the context of the **Problem-Solving & Conflict Resolution** topic.

---Goal---
Determine whether the student's message expresses a **Positive**, **Neutral**, or **Negative** sentiment in the domain of conflict resolution and problem-solving.

---Sentiment Guidance for Problem-Solving---

**Negative Sentiment Indicators:**
- The student avoids or escalates conflicts.
- There is a lack of communication or friendships have ended.
- The student withdraws or uses hostile language.
- There is avoidance of family discussions or confrontations.
- The student reacts impulsively or without considering options.
- Repeated mistakes due to lack of reflection.

**Positive Sentiment Indicators:**
- The student communicates effectively using techniques like "I feel" statements.
- Seeks compromise or resolution within a reasonable timeframe.
- Expresses concerns respectfully and listens to others.
- Uses thoughtful decision-making strategies.
- Reflects on past mistakes and applies growth mindset.

**Neutral Sentiment Indicators:**
- Descriptive or factual statements that are emotionally flat.
- Reflecting on a conflict without showing strong emotional tone.
- Sharing observations or behaviors without positive or negative interpretation.

---Conversation History---
{history}

(The history above includes previous messages from both the student and the coach. Use this to understand the emotional and behavioral context.)

---Student's Last Message---
"{last_message}"

---Instructions---
- Use the history to inform whether the message shows growth, impulsivity, avoidance, or reflection.
- Choose the **most dominant sentiment** in the context of Problem-Solving.

---Response Format---
Provide the result as a string:
<Positive | Neutral | Negative> : <1-2 sentences explaining your rationale>

Example:
Negative : The student describes avoiding a conflict and not speaking to a friend for days, showing lack of resolution or communication.
"""
