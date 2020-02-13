# encoding: UTF-8

import psycopg2
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RoamonAlertDb():
    def __init__(self):
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.dbname = None

        self.__rov_result_table_name = "rov_results"

        self.conn = None

    def connect(self, host, port, dbname, username, password):
        if self.conn is not None:
            self.conn.close()

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.dbname = dbname
        self.conn = psycopg2.connect(host=self.host, port=str(self.port), database=self.dbname, user=self.username, password=self.password)

    def init_table(self):
        if self.conn.cursor() is None:
            logger.error("connection is not established")
            return

        cur = self.conn.cursor()
        cur.execute("select * from information_schema.tables where table_name=%s", (self.__rov_result_table_name,))
        does_exist_rov_result_table = bool(cur.rowcount)

        if not does_exist_rov_result_table:
            logger.debug("Rov table is not exist. Create table...")
            cur.execute("""
                create table %s (
                  prefix varchar(32),
                  advertised_prefix  varchar(32),
                  advertising_asn integer, 
                  rov_status varchar(32),
                  data_fetched_at timestamp,
                  PRIMARY KEY (data_fetched_time, prefix)
                );
            """, (
                psycopg2.extensions.AsIs(self.__rov_result_table_name),
            ))
        self.conn.commit()
        cur.close()

    def write_db_prefix_rov_result_structs(self, prefix_rov_result_struct_list, data_fetched_time):
        if self.conn.cursor() is None:
            logger.error("connection is not established")
            return

        cur = self.conn.cursor()

        for prefix_rov_result_struct in prefix_rov_result_struct_list:
            cur.execute("""
                INSERT INTO %s
                VALUES (%s, %s, %s, %s, %s);
            """, (
                psycopg2.extensions.AsIs(self.__rov_result_table_name),
                prefix_rov_result_struct.roved_prefix,
                prefix_rov_result_struct.matched_advertised_prefix if prefix_rov_result_struct.matched_advertised_prefix is not None else psycopg2.extensions.AsIs("NULL"),
                prefix_rov_result_struct.advertising_asn if prefix_rov_result_struct.advertising_asn is not None else psycopg2.extensions.AsIs("NULL"),
                str(prefix_rov_result_struct.rov_result),
                data_fetched_time
            ))
        logger.debug("finish write DB rov result")
        # cur.fetchone()
        self.conn.commit()
        cur.close()



