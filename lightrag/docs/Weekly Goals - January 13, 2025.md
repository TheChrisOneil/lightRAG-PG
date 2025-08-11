# **LightRAG Retrieval System Testing Plan - Week 2**
**Date: January 13, 2025**

## **Objective**
Test the system's ability to interpret and retrieve information from the uploaded corpus and student dialogs through the Retrieval chatbot interface.

## **Background**
Last week, the student uploaded:
- Document corpus 
- Student dialog data

This week, we need to systematically test how well the system can retrieve and interpret this information through different query modes and parameters.

---

## **Retrieval Interface Overview**

The Retrieval page is located in the webUI and provides a comprehensive testing environment for the RAG (Retrieval-Augmented Generation) system. The interface includes a chat area and a detailed parameter panel on the right side.

---

## **Testing Parameters - Complete List**

### **1. Query Mode**
**Parameter:** `mode`  
**Options:** `naive`, `local`, `global`, `hybrid`  
**Purpose:** Controls the retrieval strategy

**Testing Tasks:**
- [ ] Test with `naive` mode - basic retrieval without graph knowledge
- [ ] Test with `local` mode - focuses on local entity relationships
- [ ] Test with `global` mode - considers broader knowledge graph connections
- [ ] Test with `hybrid` mode - combines local and global approaches
- [ ] Compare response quality across all modes using the same query
- [ ] Document which mode works best for different types of questions

### **2. Only Need Context**
**Parameter:** `only_need_context`  
**Type:** Boolean toggle  
**Purpose:** Returns only the retrieved context without generating a response

**Testing Tasks:**
- [ ] Toggle ON: Test to see raw retrieved context for queries
- [ ] Toggle OFF: Test full response generation
- [ ] Compare context quality vs. final responses
- [ ] Verify context relevance to uploaded documents

### **3. Response Type**
**Parameter:** `response_type`  
**Options:** `Multiple Paragraphs`, `Single Paragraph`, `Single Sentence`, `Keywords Only`  
**Purpose:** Controls the format and length of responses

**Testing Tasks:**
- [ ] Test `Multiple Paragraphs` for complex questions
- [ ] Test `Single Paragraph` for medium complexity
- [ ] Test `Single Sentence` for simple queries
- [ ] Test `Keywords Only` for topic identification
- [ ] Evaluate which format best preserves information from uploaded corpus


---

## **Systematic Testing Approach**

### **Phase 1: Baseline Testing (Day 1-2)**
1. **Document Verification**
   - [ ] Verify all uploaded documents are accessible
   - [ ] Test basic queries about known content from uploaded materials
   - [ ] Establish baseline performance with default settings

2. **Parameter Familiarization**
   - [ ] Test each parameter individually with simple queries
   - [ ] Document the behavior of each setting
   - [ ] Create reference examples for each parameter

### **Phase 2: Mode Comparison Testing (Day 2-3)**
1. **Prepare Test Queries**
   - [ ] Create 5-10 test questions directly related to uploaded content
   - [ ] Include questions about student dialogs
   - [ ] Include questions about document corpus
   - [ ] Mix factual and analytical questions

2. **Mode Testing Matrix**
   - [ ] Run each test query through all 4 modes
   - [ ] Document response quality and relevance
   - [ ] Note response time for each mode
   - [ ] Identify optimal modes for different query types

### **Phase 3: Response Format Testing (Day 3-4)**
1. **Format Effectiveness**
   - [ ] Test same queries with different response types
   - [ ] Evaluate information retention across formats
   - [ ] Test user readability and comprehension
   - [ ] Document format recommendations for different use cases

### **Phase 4: Advanced Parameter Combinations (Day 4-5)**
1. **Optimal Configuration Discovery**
   - [ ] Test combinations of parameters
   - [ ] Identify best configurations for different scenarios
   - [ ] Test edge cases and complex queries
   - [ ] Document performance patterns

### **Phase 5: Real-World Scenario Testing (Day 5)**
1. **Student Dialog Analysis**
   - [ ] Query about specific student interactions
   - [ ] Test system's understanding of conversation context
   - [ ] Verify retrieval of relevant dialog segments

2. **Document Knowledge Testing**
   - [ ] Test cross-document information synthesis
   - [ ] Query about relationships between different documents
   - [ ] Test system's ability to provide comprehensive answers


## **Success Metrics**

### **Technical Performance**
- [ ] Response time under 10 seconds for most queries
- [ ] Relevant context retrieval from uploaded documents
- [ ] Consistent behavior across parameter settings
- [ ] No system errors or crashes during testing

### **Content Quality**
- [ ] Responses accurately reflect uploaded content
- [ ] System demonstrates understanding of document relationships
- [ ] Student dialog context is properly retrieved and utilized
- [ ] Cross-document synthesis works effectively


---

## **Expected Outcomes**

By the end of this week, the intern should have:

1. **Complete understanding** of all Retrieval page parameters
2. **Documented evidence** of how well the system interprets uploaded content
3. **Best practice recommendations** for parameter usage
4. **Identified optimization opportunities** for future improvements
5. **Validated system readiness** for production use with student data

---

## **Next Week Preview**

Based on this week's testing results, next week will focus on:
- Optimizing retrieval performance based on findings
- Advanced query techniques
- Integration testing with other system components
- Preparing user documentation and training materials

---

**Note:** This testing plan ensures comprehensive evaluation of the LightRAG retrieval system's ability to effectively utilize the uploaded corpus and student dialog data through systematic parameter testing and real-world scenario validation.
