import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { CrawlerService, CrawlJob, Document } from '../../core/services/crawler.service';
import { AddJobDialogComponent } from './add-job-dialog';

@Component({
  selector: 'app-crawler',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatIconModule,
    MatButtonModule,
    MatTabsModule,
    MatDialogModule,
    MatSnackBarModule
  ],
  templateUrl: './crawler.html',
  styleUrl: './crawler.scss'
})
export class CrawlerComponent implements OnInit {
  jobColumns: string[] = ['source', 'query', 'schedule', 'status', 'actions'];
  docColumns: string[] = ['title', 'source', 'processed', 'date'];

  jobs: CrawlJob[] = [];
  documents: Document[] = [];

  constructor(
    private crawlerService: CrawlerService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.refreshJobs();
    this.refreshDocs();
  }

  refreshJobs() {
    this.crawlerService.getJobs().subscribe({
      next: (data) => this.jobs = data,
      error: () => {
        this.jobs = [];
      }
    });
  }

  refreshDocs() {
    this.crawlerService.getDocuments().subscribe({
      next: (data) => this.documents = data,
      error: () => {
        this.documents = [];
      }
    });
  }

  openAddJobDialog() {
    const dialogRef = this.dialog.open(AddJobDialogComponent, {
      width: '500px',
      maxWidth: '90vw',
      autoFocus: false
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.crawlerService.createJob(result).subscribe({
          next: () => {
            this.snackBar.open('Crawl job created successfully!', 'Close', { duration: 3000 });
            this.refreshJobs();
          },
          error: (err) => {
            this.snackBar.open('Failed to create job: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
          }
        });
      }
    });
  }

  runJob(job: CrawlJob) {
    this.crawlerService.triggerRun(job.id).subscribe({
      next: () => {
        this.snackBar.open('Crawl triggered! Documents will appear shortly.', 'Close', { duration: 3000 });
        setTimeout(() => this.refreshDocs(), 3000);
      },
      error: (err) => {
        this.snackBar.open('Crawl failed: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
      }
    });
  }

  deleteJob(job: CrawlJob) {
    if (!confirm(`Delete crawl job "${job.source} - ${job.query}"?`)) return;

    this.crawlerService.deleteJob(job.id).subscribe({
      next: () => {
        this.snackBar.open('Job deleted.', 'Close', { duration: 3000 });
        this.refreshJobs();
      },
      error: (err) => {
        this.snackBar.open('Failed to delete: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
      }
    });
  }

  editJob(job: CrawlJob) {
    const dialogRef = this.dialog.open(AddJobDialogComponent, {
      width: '500px',
      maxWidth: '90vw',
      autoFocus: false,
      data: {
        mode: 'edit',
        job: { ...job }
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result && result.mode === 'edit') {
        this.crawlerService.updateJob(job.id, result).subscribe({
          next: () => {
            this.snackBar.open('Crawl job updated successfully!', 'Close', { duration: 3000 });
            this.refreshJobs();
          },
          error: (err) => {
            this.snackBar.open('Failed to update job: ' + (err.error?.detail || err.message), 'Close', { duration: 5000 });
          }
        });
      }
    });
  }
}
