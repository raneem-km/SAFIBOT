import pymupdf
import os

def create_bba_syllabus():
    doc = pymupdf.open()
    
    # Page 1
    p1 = doc.new_page()
    text_p1 = """SAFI AUTONOMOUS COLLEGE
DEPARTMENT OF MANAGEMENT STUDIES
CURRICULUM & SYLLABUS - SEMESTER 3
COURSE: BACHELOR OF BUSINESS ADMINISTRATION (BBA)

SUBJECT: FINANCIAL MANAGEMENT (BBA3B04)

UNIT 1: INTRODUCTION TO FINANCIAL MANAGEMENT
Meaning, nature, scope and objectives of financial management. Profit maximization vs. wealth maximization. Role of Financial Manager in modern business organization. Time value of money: compounding and discounting techniques.

UNIT 2: COST OF CAPITAL & CAPITAL STRUCTURE
Concept and significance of cost of capital. Computation of specific costs: cost of debt, cost of preference capital, cost of equity, and cost of retained earnings. Weighted Average Cost of Capital (WACC). Capital structure theories: Net Income approach, Net Operating Income approach, Traditional approach, and MM hypothesis.

UNIT 3: CAPITAL BUDGETING & WORKING CAPITAL MANAGEMENT
Capital budgeting process and evaluation techniques: Payback Period, Accounting Rate of Return (ARR), Net Present Value (NPV), Internal Rate of Return (IRR), and Profitability Index (PI). Working capital management: concepts, operating cycle, determinants of working capital, cash management models, receivables management, and inventory control techniques.

UNIT 4: DIVIDEND DECISIONS
Dividend theories: Walter's model, Gordon's model, and Modigliani-Miller irrelevance theorem. Determinants of dividend policy. Types of dividends: cash dividend, stock dividend (bonus shares), and stock split.
"""
    p1.insert_text((50, 60), text_p1, fontsize=11)
    
    # Page 2
    p2 = doc.new_page()
    text_p2 = """SAFI AUTONOMOUS COLLEGE
DEPARTMENT OF MANAGEMENT STUDIES
CURRICULUM & SYLLABUS - SEMESTER 3
COURSE: BACHELOR OF BUSINESS ADMINISTRATION (BBA)

SUBJECT: MARKETING MANAGEMENT (BBA3B05)

UNIT 1: INTRODUCTION TO MARKETING
Core marketing concepts: needs, wants, demand, customer value and satisfaction. Evolution of marketing orientations. Holistic marketing philosophy. Marketing environment: micro and macro environmental forces affecting marketing strategy.

UNIT 2: CONSUMER BEHAVIOUR & MARKET SEGMENTATION
Consumer decision making process. Psychological, social, cultural, and individual factors influencing buyer behaviour. Market segmentation: levels, patterns, bases for segmenting consumer markets. Target marketing and product positioning strategies.

UNIT 3: PRODUCT & PRICING STRATEGIES
Concept of product and product classification. New product development process. Product Life Cycle (PLC) stages and appropriate marketing strategies. Branding, packaging and labeling decisions. Pricing objectives, factors influencing pricing, pricing methods (cost-based, value-based, competition-based), and price adjustment strategies.

UNIT 4: PROMOTION MIX & DISTRIBUTION CHANNELS
Elements of integrated marketing communications: advertising, personal selling, sales promotion, public relations, and direct marketing. Designing marketing channels: channel functions, intermediary levels, channel conflict and management. Modern retail formats and e-commerce marketing.
"""
    p2.insert_text((50, 60), text_p2, fontsize=11)
    
    out_path = "data/syllabus/BBA_Semester_3_Syllabus.pdf"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    doc.close()
    print(f"Created: {out_path}")

def create_bca_syllabus():
    doc = pymupdf.open()
    
    # Page 1
    p1 = doc.new_page()
    text_p1 = """SAFI AUTONOMOUS COLLEGE
DEPARTMENT OF COMPUTER APPLICATIONS
CURRICULUM & SYLLABUS - SEMESTER 3
COURSE: BACHELOR OF COMPUTER APPLICATIONS (BCA)

SUBJECT: DATA STRUCTURES USING C++ (BCA3B01)

UNIT 1: INTRODUCTION TO DATA STRUCTURES, ARRAYS & STACKS
Classification of data structures: primitive vs. non-primitive, linear vs. non-linear. Abstract Data Types (ADT). Dynamic memory allocation in C++. Single and multi-dimensional arrays, address calculation. Stack ADT: operations (push, pop, peek), array representation of stacks. Applications of stacks: infix to postfix conversion, evaluation of postfix expressions, recursive function execution.

UNIT 2: QUEUES & LINKED LISTS
Queue ADT: FIFO operations, linear queue, circular queue, priority queue, and double-ended queue (deque). Memory representation of queues. Singly Linked List: node structure, traversal, insertion, and deletion at beginning, end, and middle. Doubly Linked List and Circular Linked List: structure and operations. Polynomial representation using linked lists.

UNIT 3: TREES AND GRAPHS
Basic tree terminology: root, leaf, height, depth, degree of node. Binary Trees: properties and representations (array and linked). Binary Tree Traversals: Inorder, Preorder, and Postorder traversals. Binary Search Trees (BST): insertion, deletion, and searching algorithms. Balanced trees: AVL Tree rotations. Graph representations: Adjacency Matrix and Adjacency List. Graph traversals: Breadth First Search (BFS) and Depth First Search (DFS). Minimum Spanning Trees: Prim's and Kruskal's algorithms. Shortest path: Dijkstra's algorithm.

UNIT 4: SEARCHING, SORTING & HASHING
Linear search and Binary search analysis. Sorting algorithms: Bubble sort, Selection sort, Insertion sort, Quick sort, Merge sort, and Heap sort. Time and space complexity comparisons. Hashing: hash functions, collision resolution techniques (separate chaining, open addressing: linear probing, quadratic probing, double hashing).
"""
    p1.insert_text((50, 60), text_p1, fontsize=11)
    
    # Page 2
    p2 = doc.new_page()
    text_p2 = """SAFI AUTONOMOUS COLLEGE
DEPARTMENT OF COMPUTER APPLICATIONS
CURRICULUM & SYLLABUS - SEMESTER 3
COURSE: BACHELOR OF COMPUTER APPLICATIONS (BCA)

SUBJECT: DATABASE MANAGEMENT SYSTEMS (BCA3B02)

UNIT 1: INTRODUCTION TO DATABASE SYSTEMS & ER MODELING
Database system concepts, 3-tier architecture, data independence. Data models: hierarchical, network, and relational. Entity-Relationship (ER) model: entities, attributes, relationships, cardinality ratios, weak entity sets, Extended ER features (specialization, generalization).

UNIT 2: RELATIONAL MODEL & RELATIONAL ALGEBRA
Relational model concepts, relational constraints: entity integrity, referential integrity. Relational Algebra operations: select, project, union, set difference, Cartesian product, join (inner join, outer join), division.

UNIT 3: SQL & NORMALIZATION
Structured Query Language (SQL): DDL, DML, DCL, TCL commands. Subqueries, joins, aggregate functions, and views. Pitfalls in relational database design. Functional dependencies, Armstrong's axioms. Normal forms: First Normal Form (1NF), Second Normal Form (2NF), Third Normal Form (3NF), and Boyce-Codd Normal Form (BCNF).

UNIT 4: TRANSACTION PROCESSING & CONCURRENCY CONTROL
Transaction concept, ACID properties, transaction states. Concurrency control: serializability, conflict and view serializability. Lock-based protocols: two-phase locking (2PL). Deadlock prevention, detection, and recovery. Database recovery techniques: log-based recovery, checkpoints.
"""
    p2.insert_text((50, 60), text_p2, fontsize=11)
    
    out_path = "data/syllabus/BCA_Semester_3_Syllabus.pdf"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    doc.close()
    print(f"Created: {out_path}")

def create_exam_timetable():
    doc = pymupdf.open()
    
    # Page 1: General Info
    p1 = doc.new_page()
    text_p1 = """SAFI AUTONOMOUS COLLEGE
OFFICE OF THE CONTROLLER OF EXAMINATIONS
END SEMESTER DEGREE EXAMINATIONS - NOVEMBER 2026
NOTIFICATION & TIME TABLE FOR UG REGULAR / SUPPLEMENTARY

Ref: SAFI/COE/EXAM/2026/112                                    Date: 15-09-2026

INSTRUCTIONS TO CANDIDATES:
1. Candidates must carry their College Identity Card and Examination Hall Ticket to the examination hall.
2. Examination session timing: Forenoon (FN) - 09:30 AM to 12:30 PM.
3. Candidates will not be permitted to enter the examination hall 30 minutes after the commencement of the exam.
4. Mobile phones, programmable calculators, and any electronic smart gadgets are strictly banned in the exam hall.
5. Hall allocations are published on department notice boards.

This master examination schedule covers BBA, BCA, BCom, and BSc programmes. Course-specific schedules follow on respective pages.
"""
    p1.insert_text((50, 60), text_p1, fontsize=11)
    
    # Page 2: BBA S3
    p2 = doc.new_page()
    text_p2 = """SAFI AUTONOMOUS COLLEGE - END SEMESTER EXAMINATIONS NOV 2026
COURSE: BBA (BACHELOR OF BUSINESS ADMINISTRATION) - SEMESTER 3

DATE & DAY          SUBJECT CODE & TITLE                      TIME                   EXAM ROOM
--------------------------------------------------------------------------------------------------
2026-10-26 (Monday)    BBA3B04 Financial Management          09:30 AM - 12:30 PM    Exam Hall 1
2026-10-28 (Wednesday) BBA3B05 Marketing Management          09:30 AM - 12:30 PM    Exam Hall 1
2026-10-31 (Saturday)  BBA3B06 Business Research Methods     09:30 AM - 12:30 PM    Exam Hall 2
2026-11-03 (Tuesday)   BBA3B07 Corporate Governance & Ethics 09:30 AM - 12:30 PM    Exam Hall 2
--------------------------------------------------------------------------------------------------
Note: Practical/viva-voce schedules will be announced by the Head of Department.
"""
    p2.insert_text((50, 60), text_p2, fontsize=11)
    
    # Page 3: BCA S3
    p3 = doc.new_page()
    text_p3 = """SAFI AUTONOMOUS COLLEGE - END SEMESTER EXAMINATIONS NOV 2026
COURSE: BCA (BACHELOR OF COMPUTER APPLICATIONS) - SEMESTER 3

DATE & DAY          SUBJECT CODE & TITLE                      TIME                   EXAM ROOM
--------------------------------------------------------------------------------------------------
2026-10-26 (Monday)    BCA3B01 Data Structures Using C++     09:30 AM - 12:30 PM    Exam Hall 3
2026-10-28 (Wednesday) BCA3B02 Database Management Systems    09:30 AM - 12:30 PM    Exam Hall 3
2026-10-31 (Saturday)  BCA3B03 Financial Accounting          09:30 AM - 12:30 PM    Exam Hall 4
2026-11-03 (Tuesday)   BCA3B04 Software Engineering          09:30 AM - 12:30 PM    Exam Hall 4
--------------------------------------------------------------------------------------------------
Note: Data Structures lab practical examination will begin on 2026-11-06.
"""
    p3.insert_text((50, 60), text_p3, fontsize=11)
    
    # Page 4: BCom S3
    p4 = doc.new_page()
    text_p4 = """SAFI AUTONOMOUS COLLEGE - END SEMESTER EXAMINATIONS NOV 2026
COURSE: BCOM (BACHELOR OF COMMERCE) - SEMESTER 3

DATE & DAY          SUBJECT CODE & TITLE                      TIME                   EXAM ROOM
--------------------------------------------------------------------------------------------------
2026-10-27 (Tuesday)   BCM3B03 Advanced Financial Accounting  09:30 AM - 12:30 PM    Exam Hall 5
2026-10-29 (Thursday)  BCM3B04 Corporate Regulations         09:30 AM - 12:30 PM    Exam Hall 5
--------------------------------------------------------------------------------------------------
"""
    p4.insert_text((50, 60), text_p4, fontsize=11)
    
    out_path = "data/timetables/SAFI_End_Semester_Exam_Timetable_Nov2026.pdf"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    doc.close()
    print(f"Created: {out_path}")

def create_academic_calendar():
    doc = pymupdf.open()
    p1 = doc.new_page()
    text_p1 = """SAFI AUTONOMOUS COLLEGE
ACADEMIC CALENDAR & KEY DATES - ODD SEMESTER 2026-27

June 15, 2026   : Commencement of Odd Semester classes (S3, S5)
August 12, 2026 : First Internal Examination starts
September 5, 2026: Teachers' Day celebrations & Cultural Club kickoff
September 20, 2026: Examination Registration begins for Nov 2026 End Semesters
October 5, 2026 : Last date for exam registration without fine
October 12, 2026: S3 Mini-Project submission deadline
October 18, 2026: SAFI Innovate Tech Fest 2026
October 26, 2026: End Semester Degree Examinations begin (BBA, BCA, BCom)
November 15, 2026: End of Odd Semester examinations
November 20, 2026: Commencement of Even Semester classes
"""
    p1.insert_text((50, 60), text_p1, fontsize=11)
    out_path = "data/academic/SAFI_Academic_Calendar_2026_27.pdf"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    doc.close()
    print(f"Created: {out_path}")

if __name__ == "__main__":
    create_bba_syllabus()
    create_bca_syllabus()
    create_exam_timetable()
    create_academic_calendar()
