
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
    const snackBar = inject(MatSnackBar);

    return next(req).pipe(
        catchError((error: HttpErrorResponse) => {
            let errorMessage = 'An unknown error occurred!';
            if (error.error instanceof ErrorEvent) {
                // Client-side error
                errorMessage = `Error: ${error.error.message}`;
            } else {
                // Server-side error
                if (error.status === 502) {
                    errorMessage = 'Service Unavailable (502). Please try again later.';
                } else if (error.status === 401) {
                    // Optional: Don't show snackbar for 401 if we redirect to login anyway
                    errorMessage = 'Unauthorized. Please login again.';
                } else if (error.status === 403) {
                    errorMessage = 'Access Denied.';
                } else if (error.status === 404) {
                    errorMessage = 'Resource not found.';
                } else if (error.status === 500) {
                    errorMessage = 'Internal Server Error.';
                } else {
                    errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
                }
            }

            snackBar.open(errorMessage, 'Close', {
                duration: 5000,
                panelClass: ['error-snackbar']
            });

            return throwError(() => error);
        })
    );
};
