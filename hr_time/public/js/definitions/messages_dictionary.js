/**
 * Messages for different ERPNEXT transactions
 * @type {Object<string, string>}
 */
 const MESSAGES = {
   preloadCheckinOptionsFailed: 'Failed to preload check-in options',
   noEmployeeIdFound: 'No employee ID found for the current user',
   breakSuccess: 'Successfully checked out for Break',
   checkoutSuccess: 'Successfully checked out for End of Work',
   checkinSuccess: 'Successfully checked in',
   checkoutFailed: 'Could not Checkout of work',
   errFetchingEmpId: 'Error fetching employee ID',
   worklogCreationSuccess: 'Worklog added successfully',
   errFetchingWorklogStatus: 'Error fetching worklog status',
   taskDescEmptyAndNoWorklogs: 'You have no Worklogs today : Task description must not be empty.'
 };

 export default MESSAGES;