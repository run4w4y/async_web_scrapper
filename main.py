import sys
import getopt
import asyncio
import logging

async def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], '', ['driver=', 'shopname=', 'baseurl=', 'useproxy'])
    except getopt.GetoptError:
        logging.error('Specify options properly')
        sys.exit(1)

    optdict = dict(opts)
    driver_str = optdict.get('--driver')
    if driver_str is None:
        logging.error('You must specify the --driver option')
        sys.exit(1)
    
    driver_module = None
    try:
        driver_module = eval(f'__import__("drivers.{driver_str}", fromlist=["{driver_str}"])') 
    except BaseException as e:
        logging.error(e)
        sys.exit(1)

    await driver_module.main(args, optdict)

if __name__ == '__main__':
    asyncio.log.logger.setLevel(logging.ERROR)
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
    logging.info('Starting scrapper')
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Finishing up...')