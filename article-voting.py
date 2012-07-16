'''
hash: ('article:id', key1, value1)
zset: ('time', key:article, score:time) article posted time
zset: ('score', key:article, score: score)
set: ('voted:article_id', user)
'''
import time

ONE_WEEK_IN_SECOND = 7 * 86400
VOTE_SCORE = 432

#voting an article
def article_vote(conn, user, article):
#article is a string, i.e. today news:id
    one_week_ago = time.time() - ONE_WEEK_IN_SECOND
    if conn.zscore('time', article) < one_week_ago:
        return          #the article is older than one week
    
    article_id = article.partition(':')[-1]
    #add user to the set attached with article id.    
    if conn.sadd('voted:' + article_id, user):  
        conn.zincrby('score', article, VOTE_SCORE)
        conn.hincrby(article, 'votes', 1)
        
#psoting aarticles
def post_article(conn, user, title, link):
    article_id = str(conn.incr('article:'))
    vote_str = 'voted:' + article_id
    #build set('voted:id', user)
    conn.sadd(vote_str, user)
    conn.expire(vote_str, ONE_WEEK_IN_SECONDS + 1)
    
    now = time.time()
    article = 'article:' + article_id
    #build hash('article:id', key1, value1)
    #hmset: hash multi set
    conn.hmset(article, {
        'title': title,
        'link': link,
        'poster': user,
        'time': now,
        'votes': 1,
        })
    #build zset('score', article_id, score), zset('time', article_id, post_time)
    conn.zadd('score:', article, now + VOTE_SCORE)
    conn.zadd('time:', article, now)
    
    return article_id

ARTICLES_PER_PAGE = 25

def get_articles(conn, page, order='score:'):
    #start index
    start = max(page-1, 0) * ARTICLES_PER_PAGE
    end = start + ARTICLES_PER_PAGE
    
    ids = conn.zrevrangebyscore(order, start, end)
    
    articles = []
    for id in ids:
        #article_data is hash
        article_data = conn.hgetall(id)
        #add new (key, value)
        article_data['id'] = id
        articles.append(article_data)
        
    return articles

'''
use a set for each group, which stores the article ids of all articles in that
group.
'''
def add_remove_groups(conn, article_id, to_add=[], to_remove=[]):
    #to_add the list of groups that article will be added.
    article = 'article:' + article_id
    for group in to_add:
        conn.sadd('group:' + group, article)
    for group in to_remove:
        conn.srem('group:' + group, article)



        