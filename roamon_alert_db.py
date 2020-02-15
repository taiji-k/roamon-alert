# encoding: UTF-8

import psycopg2
import logging
import psycopg2.extras
import atexit

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RoamonAlertDb():
    def __init__(self, host, port, dbname, username, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.username = username
        self.password = password

        # テーブル名
        self.__rov_result_table_name = "rov_results"
        self.__contact_info_destination_table_name = "contact_informations"
        self.__contact_info_watched_prefix_table_name = "watched_prefixes"
        self.__contact_info_watched_asn_table_name = "watched_asns"

        self.conn = None

        # このクラスのインスタンスが破棄されるときに自動的にDBとの接続を切りたいが、
        # psycopg2が `could not receive data from server: Bad file descriptor`とかいうエラーときどきだすのでやめていちいち切ることにした
        # atexit.register(self.disconnect)

    # DBとの接続
    def connect(self):
        if self.conn is not None:
            self.conn.close()

        self.conn = psycopg2.connect(host=self.host, port=str(self.port), database=self.dbname, user=self.username,
                                     password=self.password)

    # DBとの接続を切る
    def disconnect(self):
        if self.conn is not None:
            self.conn.close()

    # DBにテーブルが用意されてない場合にそなえ、ROV結果を格納するテーブルを作成する
    def __init_rov_result_table(self, cursor):
        cursor.execute("select * from information_schema.tables where table_name=%s", (self.__rov_result_table_name,))
        does_exist_rov_result_table = bool(cursor.rowcount)

        # TODO: prefixはIPv6が入るかもしれないが大丈夫か考える
        # TODO: VARCHARのサイズを考える
        if not does_exist_rov_result_table:
            logger.debug("Rov table is not exist. Create table...")
            cursor.execute("""
                 create table %s (
                   prefix varchar(256),
                   advertised_prefix  varchar(256),
                   advertising_asn integer, 
                   rov_status varchar(32),
                   data_fetched_at timestamp,
                   PRIMARY KEY (data_fetched_at, prefix)
                 );
             """, (
                psycopg2.extensions.AsIs(self.__rov_result_table_name),
            ))

    # DBにテーブルが用意されてない場合にそなえ、連絡先を格納するテーブルを作成する
    def __init_contact_list_tables(self, cursor):
        concatenation_column_name = "id"

        logger.debug("Create contact info tables...")
        # 連絡先と連絡先タイプを格納するテーブル。その組み合わせごとにIDを振る。
        cursor.execute("""
             create table IF NOT EXISTS %s (
               id SERIAL,
               contact_type  varchar(32) NOT NULL,
               contact_information varchar(256) NOT NULL, 
               PRIMARY KEY (%s),
               UNIQUE (contact_type, contact_information)
             );
         """, (
            psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            psycopg2.extensions.AsIs(concatenation_column_name),
        ))

        # 連絡先に振ったIDごとに, watchするprefixをもつテーブル
        cursor.execute("""
             create table IF NOT EXISTS %s (
               contact_information_id INTEGER,
               watched_prefix  varchar(256) NOT NULL, 
               PRIMARY KEY (contact_information_id, watched_prefix),
               FOREIGN KEY (contact_information_id) REFERENCES %s(%s) ON DELETE CASCADE
             );
         """, (
            psycopg2.extensions.AsIs(self.__contact_info_watched_prefix_table_name),
            psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            psycopg2.extensions.AsIs(concatenation_column_name),
        ))

        # 連絡先に振ったIDごとに, watchするASNをもつテーブル
        cursor.execute("""
             create table IF NOT EXISTS %s (
               contact_information_id INTEGER ,
               watched_asn  INTEGER NOT NULL, 
               PRIMARY KEY (contact_information_id, watched_asn),
               FOREIGN KEY (contact_information_id) REFERENCES %s(%s) ON DELETE CASCADE
             );
         """, (
            psycopg2.extensions.AsIs(self.__contact_info_watched_asn_table_name),
            psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            psycopg2.extensions.AsIs(concatenation_column_name),
        ))

    # テーブル作成をする
    def init_table(self):
        if self.conn is None:
            logger.error("connection is not established")
            return

        cur = self.conn.cursor()

        self.__init_rov_result_table(cur)
        self.__init_contact_list_tables(cur)

        self.conn.commit()
        cur.close()

    # ROVの結果をDBに書き込む
    def write_prefix_rov_result_structs(self, prefix_rov_result_struct_list, data_fetched_time):
        if self.conn is None:
            logger.error("connection is not established")
            return

        cur = self.conn.cursor()

        logger.debug("start reading rov results...")
        for prefix_rov_result_struct in prefix_rov_result_struct_list:
            logger.debug("""
                INSERT INTO {}
                VALUES ({}, {}, {}, {}, {});
            """.format(
                self.__rov_result_table_name,
                prefix_rov_result_struct.roved_prefix,
                prefix_rov_result_struct.matched_advertised_prefix if prefix_rov_result_struct.matched_advertised_prefix is not None else "NULL",
                prefix_rov_result_struct.advertising_asn if prefix_rov_result_struct.advertising_asn is not None else "NULL",
                str(prefix_rov_result_struct.rov_result),
                data_fetched_time
            ))

            cur.execute("""
                INSERT INTO %s
                VALUES (%s, %s, %s, %s, %s);
            """, (
                psycopg2.extensions.AsIs(self.__rov_result_table_name),
                prefix_rov_result_struct.roved_prefix,
                prefix_rov_result_struct.matched_advertised_prefix if prefix_rov_result_struct.matched_advertised_prefix is not None else psycopg2.extensions.AsIs(
                    "NULL"),
                prefix_rov_result_struct.advertising_asn if prefix_rov_result_struct.advertising_asn is not None else psycopg2.extensions.AsIs(
                    "NULL"),
                str(prefix_rov_result_struct.rov_result),
                data_fetched_time
            ))
        logger.debug("finish write DB rov result")

        self.conn.commit()
        cur.close()

    # 連絡先情報を全て取得する
    def get_all_contact_info(self):
        if self.conn is None:
            logger.error("connection is not established")
            return

        cur = self.conn.cursor()

        cur.execute("""
                    SELECT * FROM %(tab_contacts)s
                """,
                    {
                        "tab_contacts": psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
                    })

        sql_result = cur.fetchall()

        self.conn.commit()
        cur.close()

        return sql_result

    # 連絡先情報を書き込む
    def write_contact_info(self, contact_type, contact_dest, watched_prefix_list, watched_asn_list):
        if self.conn is None:
            logger.error("connection is not established")
            return

        cur = self.conn.cursor()

        # 連絡先情報をINSERT
        cur.execute("""
            INSERT INTO %s
            VALUES (DEFAULT, %s, %s) ON CONFLICT DO NOTHING;
        """, (
            psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            contact_type,
            contact_dest
        ))

        # さきほどの連絡先に振られたIDを取得
        cur.execute("""
            SELECT id FROM %s WHERE contact_type = %s AND contact_information = %s;
        """, (
            psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            contact_type,
            contact_dest
        ))
        contact_information_id = int(cur.fetchone()[0])
        logger.debug("get contact info id: {}".format(contact_information_id))

        # watched prefixらをINSERT
        if watched_prefix_list is not None:
            for watched_prefix in watched_prefix_list:
                cur.execute("""
                    INSERT INTO %s
                    VALUES (%s, %s) ON CONFLICT DO NOTHING;
                """, (
                    psycopg2.extensions.AsIs(self.__contact_info_watched_prefix_table_name),
                    contact_information_id,
                    watched_prefix
                ))

        # watched ASNらをINSERT
        if watched_asn_list is not None:
            for watched_asn in watched_asn_list:
                cur.execute("""
                    INSERT INTO %s
                    VALUES (%s, %s) ON CONFLICT DO NOTHING;
                """, (
                    psycopg2.extensions.AsIs(self.__contact_info_watched_asn_table_name),
                    contact_information_id,
                    int(watched_asn)
                ))

        logger.debug("finish write contact info to DB")
        self.conn.commit()
        cur.close()

    # 連絡先情報を削除
    def delete_contact_info(self, contact_type, contact_dest, delete_target_prefix_list=None,
                            delete_target_asn_list=None):
        if self.conn is None:
            logger.error("connection is not established")
            return

        cur = self.conn.cursor()

        # 削除する連絡先(contact_type, contact_dest)のIDを取得
        cur.execute("""
            SELECT
                id
            FROM
                %s
            WHERE
                contact_type = %s
            AND contact_information = %s
            ;
        """, (
            psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            contact_type,
            contact_dest
        ))
        sql_result_contact_information_id = cur.fetchone()
        # もし削除したかった連絡先が存在しなかった場合
        if len(sql_result_contact_information_id) == 0:
            logger.error("this contact info is not exist.")
            return
        contact_information_id = int(sql_result_contact_information_id[0])

        # 指定されたprefixらをDELETE
        if delete_target_prefix_list is not None:
            for delete_target_prefix in delete_target_prefix_list:
                cur.execute("""
                    DELETE FROM %s
                    WHERE %s = %s AND %s = %s;
                """, (
                    psycopg2.extensions.AsIs(self.__contact_info_watched_prefix_table_name),
                    psycopg2.extensions.AsIs("contact_information_id"),
                    contact_information_id,
                    psycopg2.extensions.AsIs("watched_prefix"),
                    delete_target_prefix
                ))

        # 指定されたASNらをDELETE
        if delete_target_asn_list is not None:
            for delete_target_asn in delete_target_asn_list:
                cur.execute("""
                    DELETE FROM %s
                    WHERE %s = %s AND %s = %s;
                """, (
                    psycopg2.extensions.AsIs(self.__contact_info_watched_asn_table_name),
                    psycopg2.extensions.AsIs("contact_information_id"),
                    contact_information_id,
                    psycopg2.extensions.AsIs("watched_asn"),
                    delete_target_asn
                ))

        # 現在、指定された連絡先(contact_type, contact_dest)が登録してるwatched_prefixやwatched_asnが0の場合、連絡先自体も消す
        cur.execute("""
            SELECT * FROM %(tab_prefix)s WHERE %(concat_key_col)s = %(target_id)s
            UNION ALL
            SELECT * FROM %(tab_asn)s WHERE %(concat_key_col)s = %(target_id)s
        """,
                    {
                        "tab_asn": psycopg2.extensions.AsIs(self.__contact_info_watched_asn_table_name),
                        "tab_prefix": psycopg2.extensions.AsIs(self.__contact_info_watched_prefix_table_name),
                        "timestamp_col_in_tab_rov_results": psycopg2.extensions.AsIs("data_fetched_at"),
                        "concat_key_col": psycopg2.extensions.AsIs("contact_information_id"),
                        "target_id": contact_information_id
                    })
        count_len_watched_prefix_or_asn = len(cur.fetchall())
        does_have_watched_prefix_or_asn = count_len_watched_prefix_or_asn > 0

        does_have_specified_target_prefix_or_asn_list = (delete_target_prefix_list is not None) or (
                delete_target_asn_list is not None)

        # 削除の結果、連絡先に関するwatched_prefixやwatched_asnが全くなくなった場合、または削除対象のwatched_prefixかasnが全く指定されてないとき、連絡先自体を削除する
        if (not does_have_watched_prefix_or_asn) or (not does_have_specified_target_prefix_or_asn_list):
            cur.execute("""
                DELETE FROM %(tab_contacts)s WHERE id = %(target_id)s ;
            """,
                        {
                            "tab_contacts": psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
                            "target_id": contact_information_id
                        })

        self.conn.commit()
        cur.close()

    # 登録されたwatched_prefixについて、ROV結果の中でROVに失敗(ステータスがVALID以外)してるレコードがないか調べ、
    # あれば連絡先と失敗内容を返す
    def pickup_rov_failed_contact_info_about_watched_prefix(self):
        if self.conn is None:
            logger.error("connection is not established")
            return

        # dict形式で返すようにする(意味あるか不明)
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # watched_prefixとなってるprefixについて、最新のROV結果がVALID以外(=失敗)してるやつがないか調べ、連絡先情報と結合して返す
        cur.execute("""
            SELECT
                *
            FROM
                %(tab_contact)s
                INNER JOIN
                    (
                        /* watched_prefix一覧のテーブルに含まれてるprefixに関して、ROV結果テーブルから探して、最新かつ結果がVALIDでないものをリストアップ*/
                        SELECT
                            *
                        FROM
                            %(tab_prefix)s
                            INNER JOIN
                                %(tab_rov_results)s
                            ON  %(tab_prefix)s.%(prefix_col_in_tab_prefix)s = %(tab_rov_results)s.%(prefix_col_in_tab_rov_results)s
                            AND %(tab_rov_results)s.%(rov_result_col_in_tab_rov_results)s <> 'VALID'
                        WHERE
                            %(tab_rov_results)s.%(timestamp_col_in_tab_rov_results)s = (
                                SELECT
                                    max(%(timestamp_col_in_tab_rov_results)s)
                                FROM
                                    %(tab_rov_results)s
                            )
                    ) AS %(tab_subquery_failed_rov_results)s
                ON  %(tab_contact)s.%(key_col_in_tab_contact)s = %(tab_subquery_failed_rov_results)s.%(concat_key_col_in_tab_prefix)s
            ;
         """, {
            "tab_contact": psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            "tab_prefix": psycopg2.extensions.AsIs(self.__contact_info_watched_prefix_table_name),
            "tab_rov_results": psycopg2.extensions.AsIs(self.__rov_result_table_name),
            "tab_subquery_failed_rov_results": psycopg2.extensions.AsIs("failed_rov_results"),
            "prefix_col_in_tab_prefix": psycopg2.extensions.AsIs("watched_prefix"),
            "prefix_col_in_tab_rov_results": psycopg2.extensions.AsIs("prefix"),
            "timestamp_col_in_tab_rov_results": psycopg2.extensions.AsIs("data_fetched_at"),
            "concat_key_col_in_tab_prefix": psycopg2.extensions.AsIs("contact_information_id"),
            "key_col_in_tab_contact": psycopg2.extensions.AsIs("id"),
            "rov_result_col_in_tab_rov_results": psycopg2.extensions.AsIs("rov_status"),
        })

        sql_result_dict = cur.fetchall()

        logger.debug("finish sql querying")

        self.conn.commit()
        cur.close()

        # 連絡先と、そこに連絡すべき失敗内容のdictを作る
        result_dict = {}
        for row in sql_result_dict:
            contact_type = row[1]
            contact_dest = row[2]
            contact_info = (contact_type, contact_dest)
            if contact_info not in result_dict:
                result_dict[contact_info] = list()
            result_dict[contact_info].append(row)

        return result_dict

    # 登録されたwatched_asnについて、ROV結果の中でROVに失敗(ステータスがVALID以外)してるレコードがないか調べ、
    # あれば連絡先と失敗内容を返す
    def pickup_rov_failed_contact_info_about_watched_asn(self):
        if self.conn is None:
            logger.error("connection is not established")
            return

        # dict形式で返すようにする
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # watched_asnになってるasnについて、最新のROV結果がVALID以外(=失敗)してるやつがないか調べ、連絡先情報と結合して返す
        cur.execute("""
            SELECT
                *
            FROM
                %(tab_contact)s
                INNER JOIN
                    (
                        /* watched_asn一覧のテーブルに含まれてるasnに関して、ROV結果テーブルから探して、最新かつ結果がVALIDでないものをリストアップ*/
                        SELECT
                            *
                        FROM
                            %(tab_asn)s
                            INNER JOIN
                                %(tab_rov_results)s
                            ON  %(tab_asn)s.%(asn_col_in_tab_asn)s = %(tab_rov_results)s.%(asn_col_in_tab_rov_results)s
                            AND %(tab_rov_results)s.%(rov_result_col_in_tab_rov_results)s <> 'VALID'
                        WHERE
                            %(tab_rov_results)s.%(timestamp_col_in_tab_rov_results)s = (
                                SELECT
                                    max(%(timestamp_col_in_tab_rov_results)s)
                                FROM
                                    %(tab_rov_results)s
                            )
                    ) AS %(tab_subquery_failed_rov_results)s
                ON  %(tab_contact)s.%(key_col_in_tab_contact)s = %(tab_subquery_failed_rov_results)s.%(concat_key_col_in_tab_asn)s
            ;
          """, {
            "tab_contact": psycopg2.extensions.AsIs(self.__contact_info_destination_table_name),
            "tab_asn": psycopg2.extensions.AsIs(self.__contact_info_watched_asn_table_name),
            "tab_rov_results": psycopg2.extensions.AsIs(self.__rov_result_table_name),
            "tab_subquery_failed_rov_results": psycopg2.extensions.AsIs("failed_rov_results"),
            "asn_col_in_tab_asn": psycopg2.extensions.AsIs("watched_asn"),
            "asn_col_in_tab_rov_results": psycopg2.extensions.AsIs("advertising_asn"),
            "timestamp_col_in_tab_rov_results": psycopg2.extensions.AsIs("data_fetched_at"),
            "concat_key_col_in_tab_asn": psycopg2.extensions.AsIs("contact_information_id"),
            "key_col_in_tab_contact": psycopg2.extensions.AsIs("id"),
            "rov_result_col_in_tab_rov_results": psycopg2.extensions.AsIs("rov_status"),
        })

        sql_result_dict = cur.fetchall()

        logger.debug("finish write contact info to DB")

        self.conn.commit()
        cur.close()

        # 連絡先と、そこに連絡すべき失敗内容のdictを作る
        result_dict = {}
        for row in sql_result_dict:
            contact_type = row[1]
            contact_dest = row[2]
            contact_info = (contact_type, contact_dest)
            if contact_info not in result_dict:
                result_dict[contact_info] = list()
            result_dict[contact_info].append(row)
        return result_dict

        return result_dict
