CREATE TABLE STATE_DEFINITION(
    STATE_ID    NUMBER NOT NULL,
    WORKFLOW_TYPE  VARCHAR2(256) NOT NULL,
    STATE_NAME  VARCHAR2(256) NOT NULL,
    CRITERIA    VARCHAR2(512),
    PRIMARY KEY(STATE_ID)
);

CREATE UNIQUE INDEX I_STATE_DEFINITION ON STATE_DEFINITION(WORKFLOW_TYPE, STATE_NAME);

CREATE TABLE STATE_WORKFLOW(
    STATE_ID  NUMBER NOT NULL,
    NEXT_STATE_ID NUMBER,
    FOREIGN KEY(STATE_ID) REFERENCES STATE_DEFINITION(STATE_ID)
    FOREIGN KEY(NEXT_STATE_ID) REFERENCES STATE_DEFINITION(STATE_ID)
);

CREATE TABLE WORKFLOW_DEFINITION(
    WORKFLOW_ID  NUMBER NOT NULL,
    WORKFLOW_TYPE VARCHAR2(256) NOT NULL,
    EMAIL_NOTIFICATION CHAR(1) DEFAULT 'N',
    EMAIL_SUBJECT      VARCHAR2(1024),
    EMAIL_CONTENT      VARCHAR2(2048),
    PRIMARY KEY(WORKFLOW_ID)
);


CREATE TABLE STATE_HISTORY (
    REC_ID VARCHAR2(256) NOT NULL,
    STATE_ID NUMBER NOT NULL,
    NOTES   VARCHAR2(2048),
    USERID  VARCHAR2(100) NOT NULL,
    INSERT_TS  TIMESTAMP NOT NULL,
    FOREIGN KEY(STATE_ID) REFERENCES STATE_DEFINITION(STATE_ID)
);

CREATE INDEX I_STATE_HISTORY ON STATE_HISTORY(REC_ID);