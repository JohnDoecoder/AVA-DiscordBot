import random


def get_meme(reddit, guild_id: int):
    # The subreddits to choose from
    subreddits = [reddit.subreddit('deutschememes'), reddit.subreddit('cleanmemes'),
                  reddit.subreddit('MemeDerWoche/'), reddit.subreddit('memes')]

    # Go through all subreddits in a random order and pull 100 latest posts
    random.shuffle(subreddits)
    for subreddit in subreddits:
        for submission in subreddit.new(limit=50):
            new_meme = check_post(guild_id, submission)

            # Returned an error
            if new_meme is None:
                return None
            # Meme wasn't new, continue search
            if not new_meme:
                continue

            # New meme found - Add url to already shown memes
            with open(f'guilds/{guild_id}/logs/memes.txt', 'a') as urls:
                urls.write(submission.url + '\n')

            return submission

    # No new meme was found
    return 'All memes for today were already shown!'


def check_post(guild_id: int, post):
    # Open file with all meme urls
    try:
        with open(f'guilds/{guild_id}/logs/memes.txt', 'r') as urls:
            urls_text = urls.read()
    except FileNotFoundError:
        print(f'ERROR: guilds/{guild_id}/logs/memes.txt not found')
        return None

    # Meme has already been shown or Meme is not an image
    if post.url in urls_text or "https://i.redd.it/" not in post.url:
        return False

    return True
