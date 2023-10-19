from CalendarAPI.cal_setup import get_calendar_service


def get_primary_calendar(service):

    calendar = service.calendars().get(calendarId='primary').execute()

    return calendar


def add_event(summary, description, start, end, ):

    service = get_calendar_service()

    event = {
        "summary": summary,
        "description": description,
        "colorId": 7,
        "start":
            {"dateTime": start,
             "timeZone": 'GMT-04:00'
             },
            "end":
            {"dateTime": end,
             "timeZone": 'GMT-04:00'
             },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email',
                 'minutes': 3 * 24 * 60},
                {'method': 'popup',
                 'minutes': 3 * 24 * 60},
                {'method': 'email',
                 'minutes': 1 * 24 * 60},
                {'method': 'popup',
                 'minutes': 1 * 24 * 60},
            ],
        }
    }

    event = service.events().insert(calendarId='primary', body=event).execute()


def check_if_event_exisits(time_start, time_end):

    service = get_calendar_service()

    events_result = service.events().list(calendarId='primary',
                                          timeMin=f"{time_start}", timeMax=f"{time_end}").execute()

    return events_result
