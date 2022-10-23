use computervision;

CREATE TABLE Papers (
    PaperID varchar(255) PRIMARY KEY,
    Title varchar(524),
    Arxiv_link varchar(255),
    Pub_Year SMALLINT,
    Category varchar(255),
    isReview BOOLEAN,
    isConference BOOLEAN,
    isJournalArticle BOOLEAN,
    ReferenceCount int,
    CitationCount int,
    journalName varchar(255),
    Leaf BOOLEAN,
    url varchar(255)
);

CREATE TABLE Authors (
    AuthorID varchar(255) PRIMARY KEY,
    Name varchar(255),
    Affiliations varchar(255),
    PaperCount int DEFAULT 0,
    hIndex int DEFAULT 0
);

CREATE TABLE referencedBy (
    ReferenceID varchar(255) NOT NULL,
    ReferencedByID varchar(255) NOT NULL,
    NumberOfTime int,
    FOREIGN KEY (ReferenceID) REFERENCES Papers(PaperID),
    FOREIGN KEY (ReferencedByID) REFERENCES Papers(PaperID)
);

CREATE TABLE authoredBy (
    PaperID varchar(255) NOT NULL,
    AuthoredByID Varchar(255) NOT NULL,
    FOREIGN KEY (PaperID) REFERENCES Papers(PaperID),
    FOREIGN KEY (AuthoredByID) REFERENCES Authors(AuthorID)
);