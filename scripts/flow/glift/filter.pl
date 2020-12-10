#! /usr/bin/env perl

package Main;
use feature qw(say);
use strict;
use warnings;
use Getopt::Long qw(GetOptions);

{
    my $regex_id = 2;
    GetOptions("regex=i" => \$regex_id) or die "Bad command line.\n";
    die "Bad arguments." if @ARGV != 2;
    my $well_name = shift @ARGV;
    my $fn = shift @ARGV;
    my $self = Main->new(
        fn        => $fn,
        regex     => $regex_id,
        well_name => $well_name,
    );
    my $regex = $self->get_regex();
    open ( my $fh, '<', $fn ) or die "Could not open file '$fn': $!";
    while( my $line = <$fh> ) {
        chomp $line;
        say $line if $line =~ $regex;
    }
    close $fh;
}

sub get_regex {
    my ( $self ) = @_;

    my $method = "get_regex" . $self->{regex};
    if ( !$self->can($method) ) {
        die "Unknown regex id: ", $self->{regex}, "\n";
    }
    my $rx_ar = $self->$method();
    my $regex = join "|", map { "(?:". $_ . ")" } @$rx_ar;
    return qr/$regex/;
}

sub get_regex2 {
    my ( $self ) = @_;

    return [
        qr/\Q$self->{well_name}\E/,
        qr/Time step \d+/,
        qr/Report step/,
    ]
}

sub get_regex3 {
    my ( $self ) = @_;

    return [
        qr/\Q$self->{well_name}\E (?:in|de)crease/,
        qr/\Q$self->{well_name}\E.*bhp/,
        qr/Time step \d+/,
        qr/Report step/,
    ];
}

sub new {
    my ( $class, %args ) = @_;

    return bless \%args, $class;
}
