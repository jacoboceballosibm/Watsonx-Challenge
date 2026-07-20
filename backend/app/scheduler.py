"""
Background scheduler for automated agent tasks
Runs daily at midnight to check listing expirations and mismatches
"""
import asyncio
from datetime import datetime, time
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class DailyScheduler:
    """Simple daily task scheduler"""

    def __init__(self):
        self.tasks = []
        self.running = False

    def schedule_daily(self, hour: int, minute: int, task: Callable):
        """Schedule a task to run daily at specified time"""
        self.tasks.append({
            'hour': hour,
            'minute': minute,
            'task': task
        })
        logger.info(f"Scheduled task {task.__name__} for {hour:02d}:{minute:02d}")

    async def run(self):
        """Run the scheduler loop"""
        self.running = True
        logger.info("Scheduler started")

        while self.running:
            now = datetime.now()

            # Check each scheduled task
            for scheduled in self.tasks:
                if now.hour == scheduled['hour'] and now.minute == scheduled['minute']:
                    try:
                        logger.info(f"Running scheduled task: {scheduled['task'].__name__}")
                        if asyncio.iscoroutinefunction(scheduled['task']):
                            await scheduled['task']()
                        else:
                            scheduled['task']()
                    except Exception as e:
                        logger.error(f"Error in scheduled task: {e}")

            # Sleep for 60 seconds before checking again
            await asyncio.sleep(60)

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")


# Global scheduler instance
scheduler = DailyScheduler()


async def check_all_listings_expiration():
    """
    Automated daily check for listing expirations
    Runs at midnight (00:00) every day
    """
    from app.services.seat_service import get_all_seats
    from datetime import timedelta, timezone

    logger.info("Running automated expiration check")

    all_seats = get_all_seats()
    now = datetime.now(timezone.utc)

    results = {
        '30_days': [],
        '15_days': [],
        'soon': [],  # 7 days
        'expired': []
    }

    for seat in all_seats:
        if not seat.is_active:
            continue

        days_since_update = (now - seat.updated_at).days

        if days_since_update >= 30:
            results['expired'].append(seat)
        elif days_since_update >= 23:  # 7 days until expiration
            results['soon'].append(seat)
        elif days_since_update >= 15:  # 15 days until expiration
            results['15_days'].append(seat)
        elif days_since_update >= 0:  # 30 days until expiration
            results['30_days'].append(seat)

    logger.info(f"Expiration check complete: {len(results['expired'])} expired, "
                f"{len(results['soon'])} expiring soon, "
                f"{len(results['15_days'])} at 15 days, "
                f"{len(results['30_days'])} at 30 days")

    return results


async def check_all_listings_mismatch():
    """
    Automated daily check for filled-but-posted mismatches
    Runs at midnight (00:00) every day
    """
    from app.services.seat_service import get_all_seats
    from app.services.application_service import list_applicants_for_seat

    logger.info("Running automated mismatch check")

    mismatches = []

    all_seats = get_all_seats()
    for seat in all_seats:
        if not seat.is_active:
            continue

        applicants = list_applicants_for_seat(seat.seat_id)
        selected_count = sum(1 for app in applicants if app.status == 'Selected')

        if selected_count >= seat.positions_available:
            mismatches.append({
                'seat': seat,
                'selected_count': selected_count,
                'positions_available': seat.positions_available
            })

    logger.info(f"Mismatch check complete: {len(mismatches)} mismatches found")

    return mismatches


def setup_daily_tasks():
    """Setup all daily automated tasks"""
    # Run both checks at midnight (00:00)
    scheduler.schedule_daily(0, 0, check_all_listings_expiration)
    scheduler.schedule_daily(0, 0, check_all_listings_mismatch)

    logger.info("Daily tasks configured to run at 00:00")
