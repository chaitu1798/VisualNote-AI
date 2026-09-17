from typing import Dict, Any

SAMPLE_TRANSCRIPTS: Dict[str, Dict[str, Any]] = {
    "operating_systems": {
        "title": "Introduction to Operating Systems",
        "topic": "Operating Systems",
        "text": (
            "An Operating System is system software that manages computer hardware and software resources "
            "and provides common services for computer programs. The fundamental purpose of an operating "
            "system is to execute user programs and make solving user problems easier. The core components "
            "of an operating system include process management, memory management, file system management, "
            "and I/O device management. In process management, the CPU scheduler allocates CPU time slices "
            "to active processes. Memory management tracks every byte in main memory and allocates addresses "
            "dynamically. Virtual memory allows processes to execute beyond physical RAM limits using paging "
            "and swapping. Operating systems also provide a protective layer between user space and kernel space "
            "through system calls and privileged CPU instructions."
        ),
    },
    "relational_databases": {
        "title": "Relational Databases and SQL",
        "topic": "Database Management",
        "text": (
            "A Relational Database Management System organizes data into one or more tables consisting of "
            "columns and rows. Each table possesses a primary key that uniquely identifies each record. "
            "Structured Query Language, or SQL, is the standard language for storing, manipulating, and retrieving "
            "data. In contrast to NoSQL systems, relational databases enforce strict ACID properties: Atomicity, "
            "Consistency, Isolation, and Durability, ensuring transaction reliability. Normalization is the "
            "systematic process of organizing tables to eliminate data redundancy and undesirable insertion anomalies."
        ),
    },
    "tcp_handshake": {
        "title": "Computer Networks: TCP Three-Way Handshake",
        "topic": "Computer Networks",
        "text": (
            "The Transmission Control Protocol utilizes a deterministic three-way handshake mechanism to "
            "establish a reliable connection between client and server. In step one, the client sends a SYN "
            "packet with an initial sequence number. In step two, the server receives the SYN and responds with "
            "a SYN-ACK packet, acknowledging the client's sequence number and providing its own sequence number. "
            "In step three, the client replies with an ACK packet confirming receipt. Once this exchange completes, "
            "a reliable full-duplex TCP socket is opened and application data transmission begins."
        ),
    },
    "machine_learning_metrics": {
        "title": "Machine Learning: Precision and Recall",
        "topic": "Machine Learning",
        "text": (
            "In machine learning classification, accuracy is often misleading for imbalanced datasets. "
            "Precision and Recall provide a balanced evaluation. Precision is defined by the formula: "
            "Precision = TP / (TP + FP), measuring the fraction of positive predictions that were true. "
            "Recall is defined by the formula: Recall = TP / (TP + FN), measuring the fraction of actual positives "
            "that were found. The F1 Score harmonic mean combines both metrics: F1 = 2 * (Precision * Recall) / (Precision + Recall)."
        ),
    },
}
