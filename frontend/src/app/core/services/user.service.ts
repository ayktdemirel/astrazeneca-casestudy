
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, tap, throwError } from 'rxjs';

export interface User {
    id: string;
    email: string;
    role: string;
}

const API_URL = '/api'; // Proxy handles routing

@Injectable({
    providedIn: 'root'
})
export class UserService {

    constructor(private http: HttpClient) { }

    getUsers(): Observable<User[]> {
        return this.http.get<User[]>(`${API_URL}/users`).pipe(
            tap(data => console.log('UserService: Received users', data)),
            catchError(err => {
                console.error('UserService: Error fetching users', err);
                return throwError(() => err);
            })
        );
    }

    deleteUser(id: string): Observable<void> {
        return this.http.delete<void>(`${API_URL}/users/${id}`).pipe(
            tap(() => console.log(`UserService: Deleted user ${id}`)),
            catchError(err => {
                console.error(`UserService: Error deleting user ${id}`, err);
                return throwError(() => err);
            })
        );
    }
}
