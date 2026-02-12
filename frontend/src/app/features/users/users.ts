
import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { UserService, User } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService, Subscription } from '../../core/services/notification.service';
import { SubscriptionDialogComponent } from './subscription-dialog/subscription-dialog';
import { forkJoin } from 'rxjs';

interface UserWithSubscription extends User {
    subscription?: Subscription;
}

@Component({
    selector: 'app-users',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatTableModule,
        MatIconModule,
        MatButtonModule,
        MatChipsModule,
        MatDialogModule,
        MatSnackBarModule
    ],
    templateUrl: './users.html',
    styleUrl: './users.scss'
})
export class UsersComponent implements OnInit {
    displayedColumns: string[] = ['email', 'role', 'subscription_status', 'actions'];
    dataSource: UserWithSubscription[] = [];
    loading = true;

    constructor(
        private userService: UserService,
        private notificationService: NotificationService,
        private zone: NgZone,
        private cdr: ChangeDetectorRef,
        private dialog: MatDialog,
        private snackBar: MatSnackBar,
        private authService: AuthService
    ) { }

    get isAdmin(): boolean {
        return this.authService.isAdmin;
    }

    ngOnInit() {
        this.loadUsers();
    }

    loadUsers() {
        this.loading = true;

        forkJoin({
            users: this.userService.getUsers(),
            subscriptions: this.notificationService.getSubscriptions()
        }).subscribe({
            next: ({ users, subscriptions }) => {
                this.zone.run(() => {
                    this.dataSource = users.map(user => {
                        // Find ALL subscriptions for this user
                        const userSubs = subscriptions.filter(s => s.userId === user.id);

                        // Merge them into a single "display" subscription object
                        // or pick the latest one if we assume only one valid.
                        // For MVP, merging distinct values is safer to show "what they are subscribed to"

                        const mergedSub: Subscription = {
                            userId: user.id,
                            therapeuticAreas: Array.from(new Set(userSubs.flatMap(s => s.therapeuticAreas || []))),
                            competitorIds: Array.from(new Set(userSubs.flatMap(s => s.competitorIds || []))),
                            channels: Array.from(new Set(userSubs.flatMap(s => s.channels || [])))
                        };

                        // Only assign if they actually have subscriptions
                        const hasSubs = userSubs.length > 0;
                        return { ...user, subscription: hasSubs ? mergedSub : undefined };
                    });
                    this.loading = false;
                    this.cdr.detectChanges();
                });
            },
            error: (err) => {
                this.zone.run(() => {
                    console.error('Error loading data', err);
                    this.loading = false;
                    this.cdr.detectChanges();
                });
            }
        });
    }

    openSubscriptionDialog(user: User): void {
        const dialogRef = this.dialog.open(SubscriptionDialogComponent, {
            width: '400px',
            data: user
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.notificationService.createSubscription({
                    ...result,
                    userId: user.id
                }).subscribe({
                    next: () => {
                        this.snackBar.open(`Subscribed ${user.email} successfully`, 'Close', { duration: 3000 });
                    },
                    error: () => this.snackBar.open('Failed to subscribe user', 'Close', { duration: 3000 })
                });
            }
        });
    }

    deleteUser(user: User): void {
        if (confirm(`Are you sure you want to delete user ${user.email}?`)) {
            this.userService.deleteUser(user.id).subscribe({
                next: () => {
                    this.snackBar.open(`Deleted ${user.email} successfully`, 'Close', { duration: 3000 });
                    this.loadUsers();
                },
                error: (err) => {
                    console.error('Failed to delete user', err);
                    if (err.status === 403) {
                        this.snackBar.open('You are not authorized to perform this operation.', 'Close', { duration: 5000 });
                    } else {
                        this.snackBar.open('Failed to delete: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
                    }
                }
            });
        }
    }
}
