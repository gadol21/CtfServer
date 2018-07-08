from pymongo import MongoClient


def main():
    """
    Creates an initial db
    """
    c = MongoClient()
    c.drop_database('ctf')
    db = c.ctf
    db.challenges.create_index('name')
    db.teams.create_index('name')
    db.teams.insert_one({
        "name": "omerkattan",
        "password": "SwagHamster",
        "solved": [],
        "is_admin": True
    })
    db.teams.insert_one({
        "name": "TestTeam",
        "password": "Pass",
        "solved": [],
        "is_admin": False
    })

    db.challenges.insert([{
            "category": "misc",
            "description": "How about some guessing game?<br>nc ctf326 13371<br><a href=\"/static/challenge/Guessy.zip\">files here</a>",
            "flag": "flag{My_Fl4g_1s_T0o_g00d_4u}",
            "name": "Guessy",
            "points": 100
        }])


if __name__ == '__main__':
    main()