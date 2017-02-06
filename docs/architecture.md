# Architecture Overview

MasterControl (also known as MCP) is the front-line access control system intended for Makerspaces/Hackerspaces.

MasterControl is able to run independent of member management systems, however it works really well with [aMember Pro](http://www.amember.com/) - a relatively inexpensive member management system to handle payments, access records, and general membership administration. At ENTS, we use aMember Pro (also known as AMP) for our member management and tie the records into MasterControl to have up-to-date access control over the doors.

MasterControl is intended to work with [aMember Pro](http://www.amember.com/) (also known as AMP) - a member management system to handle payments, access records, and general membership administration. At ENTS, we use aMember Pro and MasterControl to ensure that our members get unrestricted access to the space when they've paid for their membership. We allow our members 24/7 unrestricted access to the facility, and therefore MasterControl does not check any time components - only dates. [A future addition](https://github.com/ENTS-Source/MasterControl/issues/2) will allow for time-based access rules on a per-member basis.
 
## System Components

The MasterControl stack is made up of various parts. The communication layer for the various parts of the stack is some kind of Message Broker. MasterControl has been tested with [RabbitMQ](https://www.rabbitmq.com/) - the same message broker use to run the ENTS stack.

The other moving parts are as follows:
* [door-logs.py](https://github.com/ENTS-Source/rocket-sheep/blob/master/plugins/door_logs.py) plugin for [Matrix-NEB](https://github.com/matrix-org/Matrix-NEB) - handles member announcements in [Matrix](https://matrix.org) (a decentralized chat system)
  * At ENTS, we use [TangENTS](https://tang.ents.ca) for our Matrix chat client (based on Riot) and [rocket-sheep](https://github.com/ENTS-Source/rocket-sheep) as the Matrix-NEB for member engagement.
* [amember-mastercontrol](https://github.com/ENTS-Source/amember-mastercontrol) - aMember Pro plugin to push data to RabbitMQ for MasterControl

## Process Walkthrough

aMember Pro pushes membership information to RabbitMQ for a number of scenarios: 
* When a new member is added
* When a member's profile is updated (ie: name change, nickname, etc)
* When a member's payment has been processed
* When a member has been granted manual access
* When a member is deleted (strongly discouraged)
* Nightly at approximately midnight (or whenever the daily cron runs)

RabbitMQ takes in the membership data through the exchange dedicated to routing these messages. The data is routed to MasterControl's inbound queue for processing.

MasterControl takes messages out of its inbound message queue, processing them into the database cache. The cache is required so that if MasterControl loses connection to the message broker, or is restarted, membership access records (who can get into the facility) are not lost. This cache is persisted into the database and is only refreshed when new data is received.

The data MasterControl has is not a complete profile - it only knows about dates the member can get in during, their name, fob number, and basic contact information. Other information such as their address, date of birth, etc are not passed down from aMember Pro.

The membership data sits in the database until someone taps their fob to the reader. The reader sends a serial message to MasterControl for processing. MasterControl begins by attempting to find the fob number in the aMember Pro cached records table. If the member is found, it moves on to access checks to ensure the member is allowed into the facility. If the fob number is not found in that table, it checks the fallback fobs table. If the fob is found in the fallback table, MasterControl assumes the fob is permitted access.

Once the appropriate membership record is found, MasterControl verifies that the member is allowed to enter based on the resitrctions for the profile (aMember Pro profiles are based on dates, while fallback profiles are always assumed to have access). If the member is permitted access, MasterControl sends an OK response to the door lock so it can let the person in. If the member is not permitted access, MasterControl denies the door lock's request. In both cases MasterControl logs the access attempt (and who the attempt belongs to) in the access database. This record is also passed along to RabbitMQ for routing.

The access message is routed through RabbitMQ to Rocket Sheep. Rocket Sheep ignores denied access attempts, but listens for successful access attempts. If it pulls a successful access attempt off of its message queue, it checks if the member would like their presence announced to the chat room. If the member wants their presence known, it sends a notice to the configured room. Whether the member wants to be announced or not Rocket Sheep records the 10 most recent successful attempts in memory. This is so that members may query `!door last <number>` to see who has been in recently.

## ENTS stack additions

ENTS has slightly more in play for the door control system that may not apply to the general use case of MasterControl. These are documented here for reference, but are completely optional for operation.

### Reporting and Health Status

ENTS has additional reporting for detecting when MasterControl is not responding correctly or misbehaving. Using external monitoring tools to check for uptime and responsiveness and internal tools to gather stats and health checks, ENTS is able to see when MasterControl stops responding in a number of ways and is alerted when the door system fails.

Because of the stack structure for MasterControl, so long as the actual MasterControl process doesn't fail members are still able to access the facility. The cached data will eventually lead to members being denied access, however it is assumed that most incidents causing downtime for any part of the system (aMember Pro, RabbitMQ, etc) will not exceed a 24-48 hour window.
