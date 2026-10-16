BEGIN TRANSACTION;
CREATE TABLE AppReportAccess (
    AppID INTEGER NOT NULL,
    ReportID INTEGER NOT NULL,
    PRIMARY KEY (AppID, ReportID),
    FOREIGN KEY (AppID) REFERENCES Apps (AppID),
    FOREIGN KEY (ReportID) REFERENCES Reports (ReportID)
);
INSERT INTO "AppReportAccess" VALUES(1,4);
INSERT INTO "AppReportAccess" VALUES(1,5);
INSERT INTO "AppReportAccess" VALUES(2,2);
INSERT INTO "AppReportAccess" VALUES(3,4);
INSERT INTO "AppReportAccess" VALUES(3,5);
INSERT INTO "AppReportAccess" VALUES(4,1);
INSERT INTO "AppReportAccess" VALUES(4,2);
INSERT INTO "AppReportAccess" VALUES(5,3);
INSERT INTO "AppReportAccess" VALUES(6,2);
INSERT INTO "AppReportAccess" VALUES(6,3);
INSERT INTO "AppReportAccess" VALUES(7,1);
CREATE TABLE Apps (
    AppID INTEGER PRIMARY KEY,
    AppName TEXT NOT NULL,
    IsActive INTEGER NOT NULL DEFAULT 1
);
INSERT INTO "Apps" VALUES(1,'Arietis Health-AH02',1);
INSERT INTO "Apps" VALUES(2,'Arietis Health-CORE',1);
INSERT INTO "Apps" VALUES(3,'Arietis Health-CRH',1);
INSERT INTO "Apps" VALUES(4,'Arietis Health-Mainstreet',1);
INSERT INTO "Apps" VALUES(5,'Arietis Health-MHS',1);
INSERT INTO "Apps" VALUES(6,'Arietis Health-NSA',1);
INSERT INTO "Apps" VALUES(7,'Arietis Health-Palmetto',1);
CREATE TABLE Clients (
    ClientID INTEGER PRIMARY KEY,
    ClientName TEXT NOT NULL,
    GroupID INTEGER NOT NULL,
    Username TEXT NOT NULL COLLATE NOCASE,
    PasswordHash TEXT NOT NULL,
    IsActive INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (GroupID) REFERENCES Groups (GroupID)
);
INSERT INTO "Clients" VALUES(2,'AH-Core Client 1',1,'ahcore.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(3,'AH-Core Client 2',1,'ahcore.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(4,'AH-Mainstreet Client 1',2,'ahmainstreet.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(5,'AH-Mainstreet Client 2',2,'ahmainstreet.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(6,'AH-MHS Client 1',3,'ahmhs.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(7,'AH-MHS Client 2',3,'ahmhs.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(8,'AH-NSA Client 1',4,'ahnsa.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(9,'AH-NSA Client 2',4,'ahnsa.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(10,'AH-Palmetto Client 1',5,'ahpalmetto.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(11,'AH-Palmetto Client 2',5,'ahpalmetto.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(12,'AH02-CAG Client 1',6,'ah02cag.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(13,'AH02-CAG Client 2',6,'ah02cag.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(14,'AH02-Champion Client 1',7,'ah02champion.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(15,'AH02-Champion Client 2',7,'ah02champion.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(16,'AH02-Coastal Client 1',8,'ah02coastal.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(17,'AH02-Coastal Client 2',8,'ah02coastal.client2@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(18,'AH02-Extant Client 1',9,'ah02extant.client1@phimed.com','Test@123',1);
INSERT INTO "Clients" VALUES(19,'AH02-Extant Client 2',9,'ah02extant.client2@phimed.com','Test@123',1);
CREATE TABLE Groups (
    GroupID INTEGER PRIMARY KEY,
    GroupName TEXT NOT NULL,
    AppID INTEGER NOT NULL,
    RLSRole TEXT,
    IsActive INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (AppID) REFERENCES Apps (AppID)
);
INSERT INTO "Groups" VALUES(1,'AH-Core',2,NULL,1);
INSERT INTO "Groups" VALUES(2,'AH-Mainstreet',4,NULL,1);
INSERT INTO "Groups" VALUES(3,'AH-MHS',5,NULL,1);
INSERT INTO "Groups" VALUES(4,'AH-NSA',6,NULL,1);
INSERT INTO "Groups" VALUES(5,'AH-Palmetto',7,NULL,1);
INSERT INTO "Groups" VALUES(6,'AH02-CAG',1,'AH02-CAG',1);
INSERT INTO "Groups" VALUES(7,'AH02-Champion',1,'AH02-Champion',1);
INSERT INTO "Groups" VALUES(8,'AH02-Coastal',1,'AH02-Coastal',1);
INSERT INTO "Groups" VALUES(9,'AH02-Extant',1,'AH02-Extant',1);
CREATE TABLE Reports (
    ReportID INTEGER PRIMARY KEY,
    ReportName TEXT NOT NULL,
    PowerBIReportID TEXT NOT NULL COLLATE NOCASE,
    WorkspaceID TEXT NOT NULL COLLATE NOCASE,
    IsRLS INTEGER NOT NULL DEFAULT 0,
    IsActive INTEGER NOT NULL DEFAULT 1
);
INSERT INTO "Reports" VALUES(1,'Accounts Receivable','b61ee39d-c9f9-435d-b8a5-121a4564746a','067b608f-823f-4b49-b2ad-db8a23b7734d',0,1);
INSERT INTO "Reports" VALUES(2,'KPI','304622c8-04b3-44b4-a37d-253faa49a319','067b608f-823f-4b49-b2ad-db8a23b7734d',0,1);
INSERT INTO "Reports" VALUES(3,'Payments','b552332b-7f6a-4592-999b-2971e412c179','067b608f-823f-4b49-b2ad-db8a23b7734d',0,1);
INSERT INTO "Reports" VALUES(4,'Accounts Receivable - RLS','b50ac8ee-388c-4ff1-97ed-73fa7928e109','067b608f-823f-4b49-b2ad-db8a23b7734d',1,1);
INSERT INTO "Reports" VALUES(5,'Payments - RLS','7756e295-b6be-4979-8b59-d018b0264e67','067b608f-823f-4b49-b2ad-db8a23b7734d',1,1);
COMMIT;
