import sys
import os
import argparse
import json
import re

import requests
import tensorflow.compat.v1 as tf
import numpy as np
import pymysql
from pymysql_comm import UsingMysql
import time
from train.modeling import GroverModel, GroverConfig, sample
from tokenization import tokenization

##### ignore tf deprecated warning temporarily
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.logging.set_verbosity(tf.logging.DEBUG)
from tensorflow.python.util import deprecation
deprecation._PRINT_DEPRECATION_WARNINGS = False
try:
    from tensorflow.python.util import module_wrapper as deprecation
except ImportError:
    from tensorflow.python.util import deprecation_wrapper as deprecation
deprecation._PER_MODULE_WARNING_LIMIT = 0
#####

parser = argparse.ArgumentParser(description='Contextual generation (aka given some metadata we will generate articles')
parser.add_argument(
    '-metadata_fn',
    dest='metadata_fn',
    type=str,
    help='Path to a JSONL containing metadata',
)
parser.add_argument(
    '-out_fn',
    dest='out_fn',
    type=str,
    help='Out jsonl, which will contain the completed jsons',
)
parser.add_argument(
    '-input',
    dest='input',
    type=str,
    help='Text to complete',
)
parser.add_argument(
    '-config_fn',
    dest='config_fn',
    default='configs/mega.json',
    type=str,
    help='Configuration JSON for the model',
)
parser.add_argument(
    '-ckpt_fn',
    dest='ckpt_fn',
    default='../models/mega/model.ckpt',
    type=str,
    help='checkpoint file for the model',
)
parser.add_argument(
    '-target',
    dest='target',
    default='article',
    type=str,
    help='What to generate for each item in metadata_fn. can be article (body), title, etc.',
)
parser.add_argument(
    '-batch_size',
    dest='batch_size',
    default=1,
    type=int,
    help='How many things to generate per context. will split into chunks if need be',
)
parser.add_argument(
    '-num_folds',
    dest='num_folds',
    default=1,
    type=int,
    help='Number of folds. useful if we want to split up a big file into multiple jobs.',
)
parser.add_argument(
    '-fold',
    dest='fold',
    default=0,
    type=int,
    help='which fold we are on. useful if we want to split up a big file into multiple jobs.'
)
parser.add_argument(
    '-max_batch_size',
    dest='max_batch_size',
    default=None,
    type=int,
    help='max batch size. You can leave this out and we will infer one based on the number of hidden layers',
)
parser.add_argument(
    '-top_p',
    dest='top_p',
    default=0.95,
    type=float,
    help='p to use for top p sampling. if this isn\'t none, use this for everthing'
)
parser.add_argument(
    '-min_len',
    dest='min_len',
    default=1024,
    type=int,
    help='min length of sample',
)
parser.add_argument(
    '-eos_token',
    dest='eos_token',
    default=102,
    type=int,
    help='eos token id',
)
parser.add_argument(
    '-samples',
    dest='samples',
    default=5,
    type=int,
    help='num_samples',
)
def select_one(cursor):
    cursor.execute("select id from dede_archives order by id DESC limit 1;")
    data = cursor.fetchone()
    print("-- 单条记录: {0} ".format(data['id']))
    return data['id']

# 新增单条记录
def create_one(title,newstText):
    with UsingMysql(log_time=True) as um:
        id = select_one(um.cursor)+1
        times = time.strftime('%Y-%m-%d', time.localtime())
        timelangs = time.time()
        miaosu = newstText[0:30]
        sql = "INSERT INTO szfusheng_com_cn.dede_archives (id, typeid, typeid2, sortrank, flag, ismake, channel, arcrank, click, money, title, shorttitle, color, writer, source, litpic, pubdate, senddate, mid, keywords, lastpost, scores, goodpost, badpost, voteid, notpost, description, filename, dutyadmin, tackid, mtype, weight) VALUES (%s, 2, '0', %s, 'c,p', 1, 1, 0, 95, 0, %s, '', '', '富力股市网', 'http://www.szfusheng.com.cn', '/tu/4274Tybx.jpg', %s, %s, 1, %s, 0, 0, 0, 0, 0, 0, %s, '', 1, 0, 0, 0);"
        prams = (id,timelangs,title,timelangs,timelangs,title,miaosu)
        um.cursor.execute(sql,prams)
        #data
        sqlData= "INSERT INTO szfusheng_com_cn.dede_addonarticle (aid, typeid, body, redirecturl, templet, userip) VALUES (%s, 2,%s, '', '', '182.133.143.177');"
        prams = (id, str(newstText))
        um.cursor.execute(sqlData, prams)
        #Index
        sqlIndex= "INSERT INTO szfusheng_com_cn.dede_arctiny (id, typeid, typeid2, arcrank, channel, senddate, sortrank, mid) VALUES (%s, 1, '0', 0, 1, %s, %s, 1);"
        prams = (id, timelangs,timelangs)
        um.cursor.execute(sqlIndex, prams)


def select_one_keyword(cursor):
    cursor.execute("select keyword from key_20201 where iskey = 0;")
    data = cursor.fetchall()
    print("取出keywords")
    return data
def extract_generated_target(output_tokens, tokenizer):
    """
    Given some tokens that were generated, extract the target
    :param output_tokens: [num_tokens] thing that was generated
    :param encoder: how they were encoded
    :param target: the piece of metadata we wanted to generate!
    :return:
    """
    # Filter out first instance of start token
    assert output_tokens.ndim == 1

    start_ind = 0
    end_ind = output_tokens.shape[0]

    return {
        'extraction': tokenization.printable_text(''.join(tokenizer.convert_ids_to_tokens(output_tokens))),
        'start_ind': start_ind,
        'end_ind': end_ind,
    }

args = parser.parse_args()
proj_root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
vocab_file_path = os.path.join(proj_root_path, "tokenization/clue-vocab.txt")
tokenizer = tokenization.FullTokenizer(vocab_file=vocab_file_path , do_lower_case=True)
news_config = GroverConfig.from_json_file(args.config_fn)

# We might have to split the batch into multiple chunks if the batch size is too large
default_mbs = {12: 32, 24: 16, 48: 3}
max_batch_size = args.max_batch_size if args.max_batch_size is not None else default_mbs[news_config.num_hidden_layers]

# factorize args.batch_size = (num_chunks * batch_size_per_chunk) s.t. batch_size_per_chunk < max_batch_size
num_chunks = int(np.ceil(args.batch_size / max_batch_size))
batch_size_per_chunk = int(np.ceil(args.batch_size / num_chunks))

# This controls the top p for each generation.
top_p = np.ones((num_chunks, batch_size_per_chunk), dtype=np.float32) * args.top_p

tf_config = tf.ConfigProto(allow_soft_placement=True)

with tf.Session(config=tf_config, graph=tf.Graph()) as sess:
    initial_context = tf.placeholder(tf.int32, [batch_size_per_chunk, None])
    p_for_topp = tf.placeholder(tf.float32, [batch_size_per_chunk])
    eos_token = tf.placeholder(tf.int32, [])
    min_len = tf.placeholder(tf.int32, [])
    tokens, probs = sample(news_config=news_config, initial_context=initial_context,
                           eos_token=eos_token, min_len=min_len, ignore_ids=None, p_for_topp=p_for_topp,
                           do_topk=False)

    saver = tf.train.Saver()
    saver.restore(sess, args.ckpt_fn)
    print('🍺Model loaded. \nInput something please:⬇️')
    #text = input()
    #while text != "":
    with UsingMysql(log_time=True) as um:
        datakeys = select_one_keyword(um.cursor)
        for datakey in datakeys:
            for i in range(args.samples):
                print("Sample,", i + 1, " of ", args.samples)
                line = tokenization.convert_to_unicode(datakey['keyword'])
                bert_tokens = tokenizer.tokenize(line)
                encoded = tokenizer.convert_tokens_to_ids(bert_tokens)
                context_formatted = []
                context_formatted.extend(encoded)
                # Format context end

                gens = []
                gens_raw = []
                gen_probs = []

                for chunk_i in range(num_chunks):
                    tokens_out, probs_out = sess.run([tokens, probs],
                                                     feed_dict={initial_context: [context_formatted] * batch_size_per_chunk,
                                                                eos_token: args.eos_token, min_len: args.min_len,
                                                                p_for_topp: top_p[chunk_i]})

                    for t_i, p_i in zip(tokens_out, probs_out):
                        extraction = extract_generated_target(output_tokens=t_i, tokenizer=tokenizer)
                        gens.append(extraction['extraction'])

                l = re.findall('.{1,70}', gens[0].replace('[UNK]', '').replace('##', ''))
                create_one(datakey['keyword'],"\n".join(l))
                print("\n".join(l))
            print('Next try:⬇️')
            #text = input()
